# ruff: noqa: D212, D415

from pathlib import Path
from typing import Annotated

from pydantic import SecretStr, ValidationError
from rich import print as rprint
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from typer import Argument, Context, Exit, Option, Typer
from typer import run as typer_run
from ynab.configuration import Configuration

from ynamazon.amazon.models import Orders, Transaction, Transactions
from ynamazon.amazon_transactions import AmazonConfig, get_amazon_transactions
from ynamazon.exceptions import YnabSetupError
from ynamazon.main import process_transactions
from ynamazon.settings import ConfigFile, SecretApiKey, SecretBudgetId, get_settings
from ynamazon.ynab_transactions import (
    TempYnabTransaction,
    get_default_ynab_config,
    get_ynab_transactions,
    update_ynab_transaction,
)

from . import utils

cli = Typer(rich_markup_mode="rich")
cli.add_typer(utils.app, name="utils", help="[bold cyan]Utility commands[/]")


@cli.command("print-ynab")
def print_ynab_transactions(
    api_key: Annotated[
        str | None,
        Argument(
            help="YNAB API key",
            default_factory=lambda: get_settings().ynab_api_key.get_secret_value(),
        ),
    ],
    budget_id: Annotated[
        str | None,
        Argument(
            help="YNAB Budget ID",
            default_factory=lambda: get_settings().ynab_budget_id.get_secret_value(),
        ),
    ],
) -> None:
    """
    [bold cyan]Prints YNAB transactions.[/]

    [yellow i]All arguments will use defaults in .env file if not provided.[/]
    """
    console = Console()

    configuration = Configuration(access_token=api_key)
    transactions, _payee = get_ynab_transactions(
        configuration=configuration, budget_id=budget_id
    )

    console.print(f"[bold green]Found {len(transactions)} transactions.[/]")

    if not transactions:
        console.print("[bold red]No transactions found.[/]")
        exit(1)

    table = Table(title="YNAB Transactions")
    table.add_column("Date", justify="left", style="cyan", no_wrap=True)
    table.add_column("Amount", justify="right", style="green")
    table.add_column("Memo", justify="left", style="yellow")

    for transaction in transactions:
        table.add_row(
            str(transaction.var_date),
            f"${-transaction.amount_decimal:.2f}",
            transaction.memo or "n/a",
        )

    console.print(table)


@cli.command("print-amazon")
def print_amazon_transactions(
    user_email: Annotated[
        str,
        Argument(
            help="Amazon username", default_factory=lambda: get_settings().amazon_user
        ),
    ],
    user_password: Annotated[
        str,
        Argument(
            help="Amazon password",
            default_factory=lambda: get_settings().amazon_password.get_secret_value(),
        ),
    ],
    order_years: Annotated[
        list[int] | None,
        Option("-y", "--years", help="Order years; leave empty for current year"),
    ] = None,
    transaction_days: Annotated[
        int, Option("-d", "--days", help="Days of transactions to retrieve")
    ] = 31,
) -> None:
    """
    [bold cyan]Prints Amazon transactions.[/]

    [yellow i]All required arguments will use defaults in .env file if not provided.[/]
    """
    console = Console()

    config = AmazonConfig(username=user_email, password=user_password)  # type: ignore[arg-type]

    transactions = get_amazon_transactions(
        configuration=config,
        order_years=order_years,
        transaction_days=transaction_days,
    )

    console.print(f"[bold green]Found {len(transactions)} transactions.[/]")

    if not transactions:
        console.print("[bold red]No transactions found.[/]")
        exit(1)

    table = Table(title="Amazon Transactions")
    table.add_column("Completed Date", justify="left", style="cyan", no_wrap=True)
    table.add_column("Transaction Total", justify="right", style="green")
    table.add_column("Order Total", justify="right", style="green")
    table.add_column("Order Number", justify="center", style="cyan")
    table.add_column("Order Link", justify="center", style="blue underline")
    table.add_column("Item Names", justify="left", style="yellow")

    for transaction in transactions:
        table.add_row(
            str(transaction.completed_date),
            f"${transaction.transaction_total:.2f}",
            f"${transaction.order_total:.2f}",
            transaction.order_number,
            str(transaction.order_link),
            " | ".join(item.title for item in transaction.items),
        )

    console.print(table)


@cli.command()
def ynamazon(
    ynab_api_key: Annotated[
        str | None,
        Argument(
            help="YNAB API key",
            default_factory=lambda: get_settings().ynab_api_key.get_secret_value(),
        ),
    ],
    ynab_budget_id: Annotated[
        str | None,
        Argument(
            help="YNAB Budget ID",
            default_factory=lambda: get_settings().ynab_budget_id.get_secret_value(),
        ),
    ],
    amazon_user: Annotated[
        str,
        Argument(
            help="Amazon username",
            default_factory=lambda: get_settings().amazon_user,
        ),
    ],
    amazon_password: Annotated[
        str,
        Argument(
            help="Amazon password",
            default_factory=lambda: get_settings().amazon_password.get_secret_value(),
        ),
    ],
) -> None:
    """
    [bold cyan]Match YNAB transactions to Amazon Transactions and optionally update YNAB Memos.[/]

    [yellow i]All required arguments will use defaults in .env file if not provided.[/]
    """
    process_transactions(
        amazon_config=AmazonConfig(username=amazon_user, password=amazon_password),  # type: ignore[arg-type]
        ynab_config=Configuration(access_token=ynab_api_key),
        budget_id=ynab_budget_id,
    )


# TODO: modularize to simplify; or let it be complex as a "script"?
@cli.command()
def new_ynamazon(  # noqa: C901
    ynab_api_key: Annotated[str | None, Argument(help="YNAB API key")] = None,
    ynab_budget_id: Annotated[str | None, Argument(help="YNAB Budget ID")] = None,
    amazon_user: Annotated[str | None, Argument(help="Amazon username")] = None,
    amazon_password: Annotated[str | None, Argument(help="Amazon password")] = None,
    config_path: Annotated[
        Path | None, Option("-c", "--config", dir_okay=False, readable=True)
    ] = None,
    force_logout: Annotated[bool, Option()] = False,
    debug: Annotated[bool, Option("-d", "--debug", help="Enable debug mode")] = False,
    test: Annotated[bool, Option("-t", "--test", hidden=True)] = False,
) -> None:
    console = Console()
    if config_path is not None:
        config = ConfigFile.from_config(config_path)
        if ynab_api_key is not None:
            config.ynab_api_key = SecretApiKey(ynab_api_key)
        if ynab_budget_id is not None:
            config.ynab_budget_id = SecretBudgetId(ynab_budget_id)
        if amazon_user is not None:
            config.amazon_user = amazon_user
        if amazon_password is not None:
            config.amazon_password = SecretStr(amazon_password)
        cli_settings = get_settings().model_copy(update=config.model_dump())
    else:
        assert ynab_api_key is not None, "YNAB API key is required"
        assert ynab_budget_id is not None, "YNAB Budget ID is required"
        assert amazon_user is not None, "Amazon username is required"
        assert amazon_password is not None, "Amazon password is required"
        cli_settings = get_settings().model_copy(
            update={
                "ynab_api_key": SecretApiKey(ynab_api_key),
                "ynab_budget_id": SecretBudgetId(ynab_budget_id),
                "amazon_user": amazon_user,
                "amazon_password": SecretStr(amazon_password),
            }
        )

    ynab_config = get_default_ynab_config()

    try:
        ynab_trans, amazon_with_memo_payee = get_ynab_transactions(
            configuration=ynab_config,
            budget_id=cli_settings.get_secret_value("ynab_budget_id"),
        )
        console.print(f"[bold green]Found {len(ynab_trans)} transactions.[/]")
    except YnabSetupError as e:
        console.print(f"[bold red]get_settings() error: {e}[/]")
        console.print(
            "[bold red]Please check your .env file or use the --config option to specify a config file.[/]"
        )
        raise Exit(code=1) from None

    try:
        amazon_config = AmazonConfig(
            username=cli_settings.amazon_user,
            password=cli_settings.amazon_password,
            debug=debug,
        )
    except ValidationError as e:
        console.print(f"[bold red]get_settings() error: {e}[/]")
        console.print(
            "[bold red]Please check your .env file or use the --config option to specify a config file.[/]"
        )
        raise Exit(code=1) from None
    amazon_session = amazon_config.amazon_session(debug=debug)
    if not test:
        if force_logout:
            console.print("[bold cyan]Logging out of Amazon...[/]")
            amazon_session.logout()
        console.print("[bold cyan]Logging in to Amazon...[/]")
        amazon_session.login()

        console.print("[bold cyan]Retrieving Amazon orders...[/]")
        orders = Orders.get_order_history(
            amazon_config, session=amazon_session, debug=debug
        )
        console.print(f"[bold green]Found {len(orders)} orders.[/]")

        console.print("[bold cyan]Retrieving Amazon transactions...[/]")
        transactions = Transactions.get_transactions(
            config=amazon_config,
            amazon_session=amazon_session,
            transaction_days=31,
            debug=debug,
        )
        console.print(f"[bold green]Found {len(transactions)} transactions.[/]")

    else:
        orders_file = Path(
            "C:\\Users\\KW131407\\repos\\YNAmazon\\src\\ynamazon\\amazon\\orders.json"
        )
        transactions_file = Path(
            "C:\\Users\\KW131407\\repos\\YNAmazon\\src\\ynamazon\\amazon\\transactions.json"
        )
        console.print("[bold cyan]Using test data...[/]")
        orders = Orders.model_validate_json(orders_file.read_text())
        transactions = Transactions.model_validate_json(transactions_file.read_text())

    console.print("[bold cyan]Matching transactions to orders...[/]")
    transactions.match_orders(orders)

    for ynab_transaction in ynab_trans:
        transaction_date = ynab_transaction.var_date
        transaction_amount = ynab_transaction.amount_decimal
        console.print("\n\n")
        console.print(
            f"[cyan]Looking for an Amazon Transaction that matches this YNAB transaction:[/] {transaction_date} ${transaction_amount:.2f}"
        )
        matches = [
            transaction
            for transaction in transactions.items()
            if transaction_amount.compare(transaction[1].grand_total) == 0
        ]

        if not matches:
            console.print(
                "[bold yellow]**** Could not find a matching Amazon Transaction![/]"
            )
            continue
        matching_transaction = select_matching_transaction(
            ynab_transaction=ynab_transaction,
            transactions=matches,
            console=console,
        )
        if matching_transaction is None:
            console.print(
                "[bold yellow]**** Skipping and moving on to next transaction![/]"
            )
            continue
        id, untupled_transaction = matching_transaction
        console.print(
            f"[green]Matching Amazon Transaction:[/] {untupled_transaction.completed_date} ${untupled_transaction.grand_total:.2f}"
        )
        del transactions[id]

        ynab_transaction.create_memo(untupled_transaction)
        memo = ynab_transaction.rendered_memo
        console.print("[bold cyan]Memo:[/]")
        console.print(memo)

        update_transaction = Confirm.ask(
            prompt="[bold cyan]Update YNAB transaction with this memo?[/]",
            console=console,
            default=True,
        )
        if update_transaction:
            console.print("[bold cyan]Updating YNAB transaction...[/]")
            update_ynab_transaction(
                transaction=ynab_transaction,
                memo=memo,
                payee_id=amazon_with_memo_payee.id,
            )
            continue

        console.print("[bold yellow]Skipping YNAB transaction update...[/]")


def select_matching_transaction(
    ynab_transaction: TempYnabTransaction,
    transactions: list[tuple[str, Transaction]],
    console: Console | None = None,
) -> tuple[str, Transaction] | None:
    """Given an amount, locate a matching Amazon transaction.

    Args:
        ynab_transaction (TempYnabTransaction): A YNAB transaction to match
        transactions (tuple[str, Transactions]): A list of tuples of a UUID and Amazon transactions that match `ynab_transaction`
        console (Console | None): Console to use for printing. If None, a new Console will be created.

    Returns:
        tuple[str, Transaction] | None: The matching Amazon transaction or None if no match is found.
    """
    if console is None:
        console = Console()

    if len(transactions) == 1:
        return transactions[0]

    console.print(
        f"[bold cyan]Select a matching transaction for {ynab_transaction.var_date} ${ynab_transaction.amount_decimal:.2f}[/]"
    )

    matches = transactions.copy()
    matches.sort(key=lambda x: x[1].completed_date, reverse=True)
    table = Table(title="Possible Matches")
    table.add_column("Option", style="cyan")
    table.add_column("Completed Date", style="green")
    table.add_column("Order Number", style="cyan")
    valid_choices = []
    for idx, match in enumerate([trans for _, trans in matches], start=1):
        valid_choices.append(str(idx))
        match_order = match.order
        if match_order is None:
            console.print(
                f"[bold red]**** No order found for transaction {match.completed_date} ${match.grand_total:.2f}[/]"
            )
            console.log(f"Transaction: {match}")
            continue
        if match_order.order_details_link is None:
            order_number = match_order.order_number
        else:
            order_number = f"[link={match_order.order_details_link}]{match_order.order_number}[/link]"
        table.add_row(str(idx), str(match.completed_date), order_number)

    console.print(table)

    choice = Prompt.ask(
        prompt="Select the best match or 's' to skip",
        default="1",
        choices=[*valid_choices, "s"],
        case_sensitive=False,
        console=console,
    )

    return matches[int(choice) - 1] if choice != "s" else None


@cli.callback(invoke_without_command=True)
def yna_callback(ctx: Context) -> None:
    """
    [bold cyan]Run 'yna' to match and update transactions using the arguements in .env. [/]

    [yellow i]Use 'yna ynamazon [ARGS]' to use command-line arguements to override .env. [/]
    """
    rprint("[bold cyan]Starting YNAmazon processing...[/]")
    if ctx.invoked_subcommand is None:
        typer_run(function=ynamazon)
