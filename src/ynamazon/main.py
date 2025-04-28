from typing import TYPE_CHECKING

from loguru import logger
from pydantic import BaseModel, Field
from rich.console import Console
from rich.prompt import Confirm

from ynamazon.amazon_transactions import (
    AmazonConfig,
    AmazonTransactionWithOrderInfo,
    get_amazon_transactions,
    locate_amazon_transaction_by_amount,
)
from ynamazon.ynab_memo import process_memo

from .exceptions import YnabSetupError
from .settings import get_settings
from .ynab_transactions import (
    get_default_ynab_config,
    get_ynab_transactions,
    markdown_formatted_link,
    markdown_formatted_title,
    update_ynab_transaction,
)

if TYPE_CHECKING:
    from ynab.configuration import Configuration


class MultiLineText(BaseModel):
    """A class to handle multi-line text."""

    lines: list[str] = Field(default_factory=list)

    def __str__(self) -> str:
        """Returns the string representation of the object."""
        return "\n".join(self.lines)

    def append(self, line: str) -> None:
        """Appends a line to the text."""
        self.lines.append(line)


def truncate_memo(memo: str) -> str:
    """Ensure memo doesn't exceed YNAB's character limit by truncating each line proportionally.

    Args:
        memo (str): The full memo text

    Returns:
        str: Truncated memo with each line shortened proportionally if needed
    """
    max_length = 500  # YNAB's character limit

    # Keep this check for function's integrity as a standalone utility
    if len(memo) <= max_length:
        return memo

    # Split the memo into lines
    lines = memo.split("\n")

    # Calculate how many characters need to be removed
    excess_chars = len(memo) - max_length

    # Count total characters in item lines (excluding warning and URL lines)
    item_lines = []
    non_item_lines = []

    for line in lines:
        # Identify item lines (numbered items)
        if line.strip() and (line.strip()[0].isdigit() and ". " in line):
            item_lines.append(line)
        else:
            non_item_lines.append(line)

    # If no item lines found, fall back to simple truncation
    if not item_lines:
        return memo[: max_length - 12] + " [truncated]"

    # Calculate characters to remove from each item line
    chars_per_line = excess_chars // len(item_lines)

    # Truncate each item line
    new_lines = []
    for line in lines:
        if line in item_lines:
            # For numbered items, preserve the numbering, truncate the content
            parts = line.split(". ", 1)
            if len(parts) == 2 and len(parts[1]) > chars_per_line + 3:
                truncated_item = (
                    parts[0] + ". " + parts[1][: -(chars_per_line + 3)] + "..."
                )
                new_lines.append(truncated_item)
            else:
                new_lines.append(line)  # Line too short to truncate
        else:
            new_lines.append(line)  # Don't truncate non-item lines

    result = "\n".join(new_lines)

    # Final check - if we're still over the limit, do a simple truncation
    if len(result) > max_length:
        return result[: max_length - 12] + " [truncated]"

    return result


# TODO: reduce complexity of this function
def process_transactions(
    amazon_config: AmazonConfig | None = None,
    ynab_config: "Configuration | None" = None,
    budget_id: str | None = None,
) -> None:
    """Match YNAB transactions to Amazon Transactions and optionally update YNAB Memos."""
    amazon_config = amazon_config or AmazonConfig()
    ynab_config = ynab_config or get_default_ynab_config()
    budget_id = budget_id or get_settings().ynab_budget_id.get_secret_value()

    console = Console()

    try:
        ynab_trans, amazon_with_memo_payee = get_ynab_transactions(
            configuration=ynab_config, budget_id=budget_id
        )
    except YnabSetupError:
        console.print("[bold red]No matching Transactions found in YNAB. Exiting.[/]")
        return

    console.print("[cyan]Starting search for Amazon transactions...[/]")
    amazon_trans = get_amazon_transactions()
    console.print(
        f"[green]{len(amazon_trans)} Amazon transactions retrieved successfully.[/]"
    )

    console.print("[cyan]Starting to look for matching transactions...[/]")
    for ynab_tran in ynab_trans:
        console.print(
            f"[cyan]Looking for an Amazon Transaction that matches this YNAB transaction:[/] {ynab_tran.var_date} ${ynab_tran.amount / -1000:.2f}"
        )
        # because YNAB uses "milliunits" for amounts, we need to convert to dollars
        logger.debug(f"YNAB transaction amount [dollars]: {ynab_tran.amount_decimal}")
        amazon_tran_index = locate_amazon_transaction_by_amount(
            amazon_trans=amazon_trans, amount=ynab_tran.amount_decimal
        )
        if not amazon_tran_index:
            console.print(
                "[bold yellow]**** Could not find a matching Amazon Transaction![/]"
            )
            continue

        amazon_tran = amazon_trans[amazon_tran_index]
        console.print(
            f"[green]Matching Amazon Transaction:[/] {amazon_tran.completed_date} ${amazon_tran.transaction_total:.2f}"
        )

        memo = create_memo(amazon_tran)

        console.print("[bold u green]Memo:[/]")
        console.print(str(memo))

        # Process the memo and use new AI summary or trucation if needed
        memo_str = process_memo(str(memo))

        console.print("[bold u green]Processed Memo:[/]")
        console.print(memo_str)

        if amazon_tran.completed_date != ynab_tran.var_date:
            console.print(
                f"[yellow]**** The dates don't match! YNAB: {ynab_tran.var_date} Amazon: {amazon_tran.completed_date}[/]"
            )
            continue_match = Confirm.ask(
                "[bold red]Continue matching this transaction anyway?[/]",
                console=console,
            )
            if not continue_match:
                console.print("[yellow]Skipping this transaction...[/]")
                continue
            else:
                _ = amazon_trans.pop(amazon_tran_index)
                console.log("Removing matched transaction from search")

        update_transaction = Confirm.ask(
            "[bold cyan]Update YNAB transaction memo?[/]", console=console
        )
        if not update_transaction:
            console.print("[yellow]Skipping YNAB transaction update...[/]\n\n")
            console.print("[cyan i]Memo Preview[/]:")
            console.print(memo_str)
            continue

        console.print("[green]Updating YNAB transaction memo...[/]")

        update_ynab_transaction(
            transaction=ynab_tran,
            memo=memo_str,
            payee_id=amazon_with_memo_payee.id,
        )
        console.print("\n\n")


def create_memo(amazon_tran: AmazonTransactionWithOrderInfo) -> MultiLineText:
    """Creates a memo for the YNAB transaction based on the Amazon transaction."""
    memo = MultiLineText()
    if amazon_tran.transaction_total != amazon_tran.order_total:
        memo.append(
            f"-This transaction doesn't represent the entire order. The order total is ${amazon_tran.order_total:.2f}-"
        )
    if len(amazon_tran.items) > 1:
        memo.append("**Items**")
        for i, item in enumerate(amazon_tran.items, start=1):
            memo.append(f"{i}. {markdown_formatted_title(item.title, item.link)}")
    elif len(amazon_tran.items) == 1:
        item = amazon_tran.items[0]
        memo.append(f"- {markdown_formatted_title(item.title, item.link)}")

    memo.append(
        markdown_formatted_link(
            f"Order #{amazon_tran.order_number}", amazon_tran.order_link
        )
        if amazon_tran.order_link is not None
        else ""
    )

    return memo


if __name__ == "__main__":
    process_transactions()
