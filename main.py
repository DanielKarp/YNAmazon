import amazon_transactions
import ynab_transactions
from amazon_transactions import TransactionWithOrderInfo

from settings import settings

from cli_parser import CLIParser

def process_transactions() -> None:
    """Match YNAB transactions to Amazon Transactions and optionally update YNAB Memos."""
    ynab_trans, amazon_with_memo_payee = ynab_transactions.get_ynab_transactions()

    use_amazon_cache = not CLIParser().force_refresh_amazon

    if use_amazon_cache:
      print("Amazon transactions may need to be refreshed. If so, please wait as it can take a while...")
    else:
      print("Forcing refresh of Amazon transactions. Please wait as it can take a while...")

    amazon_trans: list[TransactionWithOrderInfo] = (
        amazon_transactions.get_amazon_transactions(use_cache = use_amazon_cache)
    )
    if not ynab_trans:
        print("No matching Transactions found in YNAB. Exiting.")
        return
    print("\n\n\nStarting to look for matching transactions...\n")
    for ynab_tran in ynab_trans:
        print(
            f"\n\nLooking for an Amazon Transaction that matches this YNAB transaction: {ynab_tran.var_date} ${ynab_tran.amount / -1000:.2f}"
        )
        amazon_tran: TransactionWithOrderInfo | None = find_matching_amazon_transaction(
            amazon_trans=amazon_trans, amount=ynab_tran.amount
        )
        if not amazon_tran:
            print("**** Could not find a matching Amazon Transaction!")
            continue
        print("Found a matching Amazon Transaction!")
        print(
            f"Matching Amazon Transaction: {amazon_tran.completed_date} ${amazon_tran.transaction_total / 1000:.2f}"
        )

        memo: str = ""
        if amazon_tran.transaction_total != amazon_tran.order_total:
            memo += f"-This transaction doesn't represent the entire order. The order total is ${amazon_tran.order_total / 1000:.2f}-    \n\n"
        if len(amazon_tran.item_names) > 1:
            for i, item in enumerate(amazon_tran.item_names, start=1):
                memo += f"{i}. {item}  \n"
        elif len(amazon_tran.item_names) == 1:
            memo += amazon_tran.item_names[0] + "  \n"


        memo += _formatted_link(f"Order #{amazon_tran.order_number}", amazon_tran.order_link)

        print('\nMemo:')
        print(memo)

        no: str = input(
            "\nupdate transaction? press enter to continue, type anything and press enter to skip..."
        )
        if no:
            print("skipping...\n\n")
        else:
            print("updating...")
            ynab_transactions.update_ynab_transaction(
                transaction=ynab_tran, memo=memo, payee_id=amazon_with_memo_payee.id
            )
            print("\n\n")


def _formatted_link(
    title: str,
    url: str
) -> str:
    """Returns a link in markdown or raw format, dependent on ynab_use_markdown

    Args:
        title (str): The name for the link
        url (str): The URL to link to

    Returns:
        str: A URL string suitable for injection into the memo
    """

    if settings.ynab_use_markdown:
        return f"[{title}]({url})"

    return url

 
def find_matching_amazon_transaction(
    amazon_trans: list[TransactionWithOrderInfo], amount: int
) -> TransactionWithOrderInfo | None:
    """Given an amount, locate a matching Amazon transaction.

    Args:
        amazon_trans (list[TransactionWithOrderInfo]): A list of Amazon transactions
        amount (int): An amount to match

    Returns:
        TransactionWithOrderInfo | None: A matched transaction or None if no match
    """
    amount = amount * -1
    for a_tran in amazon_trans:
        if a_tran.transaction_total == amount:
            return a_tran


if __name__ == "__main__":
    process_transactions()
