from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory
from ynab.models.budget_detail import BudgetDetail
from ynab.models.hybrid_transaction import HybridTransaction
from ynab.models.payee import Payee

from ynamazon.ynab_transactions import MemoField

fake = Faker()


def generate_item_lines(
    nb: int | None = None, nb_words: int | None = None
) -> list[tuple[int, str]]:
    nb = nb or fake.random_int(min=1, max=5)
    nb_words = nb_words or fake.random_int(min=3, max=10)
    return [(i, fake.sentence(nb_words=nb_words)) for i in range(1, nb)]


class PayeeFactory(ModelFactory[Payee]): ...


amazon_payee = PayeeFactory.build(name="Amazon")
amazon_needs_memo_payee = PayeeFactory.build(name="Amazon Needs Memo")


class BudgetFactory(ModelFactory[BudgetDetail]):
    payees = [amazon_payee, amazon_needs_memo_payee]  # noqa: RUF012


class HybridTransactionFactory(ModelFactory[HybridTransaction]): ...


class NeedsMemoHybridTransactionFactory(HybridTransactionFactory):
    payee_id: str = amazon_needs_memo_payee.id


class AmazonTransactionFactory(HybridTransactionFactory):
    payee_id: str = amazon_payee.id


class MemoFieldFactory(ModelFactory[MemoField]):
    header_lines: list[str] = fake.sentences(nb=fake.random_int(min=1, max=3))
    item_lines: list[tuple[int, str]] = generate_item_lines()
    footer_lines: list[str] = fake.sentences(nb=fake.random_int(min=1, max=3))
