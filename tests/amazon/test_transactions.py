# pyright: reportAttributeAccessIssue=false
import functools
from datetime import date, timedelta
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from amazonorders.entity.item import Item
from amazonorders.entity.order import Order
from amazonorders.session import AmazonSession
from faker import Faker
from pydantic import SecretStr

from ynamazon.amazon_transactions import (  # type: ignore[import-untyped]
    _fetch_amazon_order_history,
)
from ynamazon.settings import SecretApiKey, SecretBudgetId, Settings

if TYPE_CHECKING:
    from amazonorders.orders import AmazonOrders

fake = Faker()


@pytest.fixture
def mock_session() -> AmazonSession:
    session = MagicMock(spec=AmazonSession)
    session.is_authenticated = True
    return session


@pytest.fixture
def mock_orders() -> list[Order]:
    order1 = MagicMock(spec=Order)
    order1.order_number = "123"
    order1.order_placed_date = date(2022, 1, 1)
    order1.grand_total = 100.00

    order2 = MagicMock(spec=Order)
    order2.order_number = "456"
    order2.order_placed_date = date(2023, 1, 1)
    order2.grand_total = 200.00

    return [order1, order2]


class FakeItem:
    def __init__(self):
        self.title = fake.sentence()
        self.link = fake.url()
        self.price = fake.random_number(digits=2) + 0.99
        self.seller = "Fake Seller"
        self.condition = "New"
        self.return_eligible_date = date(2023, 1, 1) + timedelta(days=30)
        self.image_link = fake.image_url()
        self.quantity = fake.random_int(min=1, max=5)


def batch_create_items(size: int, **kwargs) -> list[Item]:
    items = []
    for _ in range(size):
        item = MagicMock(spec=Item)
        item.title = fake.sentence()
        item.link = fake.url()
        item.price = fake.random_number(digits=2) + 0.99
        item.seller = "Fake Seller"
        item.condition = "New"
        item.return_eligible_date = date(2023, 1, 1) + timedelta(days=30)
        item.image_link = fake.image_url()
        item.quantity = fake.random_int(min=1, max=5)
        items.append(item)

    return items


@pytest.fixture
def mock_amazon_many_items() -> Order:
    order = MagicMock(spec=Order)
    order.order_number = "567"
    order.order_placed_date = date(2023, 1, 1)
    order.grand_total = 200.00
    order.items = batch_create_items(size=5)

    return order


@pytest.fixture
def mock_settings() -> Settings:
    settings = MagicMock(spec=Settings)
    settings.ynab_api_key = SecretApiKey("fake_api_key")
    settings.ynab_budget_id = SecretBudgetId("fake_budget_id")
    settings.amazon_user = fake.email()
    settings.amazon_password = SecretStr("fake_password")
    settings.openai_api_key = SecretApiKey("fake_openai_key")

    return settings


def side_effect(year: int, *, mock_orders: list[Order]) -> list[Order]:
    if year == 2022:
        return [mock_orders[0]]
    elif year == 2023:
        return [mock_orders[1]]
    return []


@patch("ynamazon.amazon_transactions.AmazonOrders")
def test_fetch_amazon_order_history_with_years(
    mock_amazon_orders: "AmazonOrders",
    mock_settings,
    mock_session,
    mock_orders,
):
    side_effect_year = functools.partial(side_effect, mock_orders=mock_orders)
    mock_amazon_orders.return_value.get_order_history.side_effect = side_effect_year

    patch("ynamazon.settings.settings", mock_settings)

    result = _fetch_amazon_order_history(session=mock_session, years=[2022, 2023])

    assert len(result) == 2
    assert result[0].order_number == "123"
    assert result[1].order_number == "456"
    mock_amazon_orders.return_value.get_order_history.assert_any_call(year=2022)
    mock_amazon_orders.return_value.get_order_history.assert_any_call(year=2023)


@patch("ynamazon.amazon_transactions.AmazonOrders")
def test_fetch_amazon_order_history_two_digit_year(
    mock_amazon_orders: "AmazonOrders", mock_session, mock_orders, mock_settings
):
    patch("ynamazon.settings.settings", mock_settings)
    mock_amazon_orders.return_value.get_order_history.return_value = [mock_orders[0]]

    result = _fetch_amazon_order_history(session=mock_session, years=[22])

    assert len(result) == 1

    mock_amazon_orders.return_value.get_order_history.assert_called_once_with(year=2022)


@patch("ynamazon.amazon_transactions.AmazonOrders")
def test_fetch_amazon_order_history_two_digit_str_year(
    mock_amazon_orders: "AmazonOrders", mock_session, mock_orders, mock_settings
):
    patch("ynamazon.settings.settings", mock_settings)
    mock_amazon_orders.return_value.get_order_history.return_value = [mock_orders[0]]

    result = _fetch_amazon_order_history(session=mock_session, years=["22"])

    assert len(result) == 1

    mock_amazon_orders.return_value.get_order_history.assert_called_once_with(year=2022)


@patch(
    "ynamazon.amazon_transactions.AmazonOrders",
)
def test_fetch_amazon_order_history_no_years(
    mock_amazon_orders: "AmazonOrders",
    mock_session: AmazonSession,
    mock_orders: list[Order],
    mock_settings,
):
    patch("ynamazon.settings.settings", mock_settings)
    side_effect_year = functools.partial(side_effect, mock_orders=mock_orders)
    mock_amazon_orders.return_value.get_order_history.side_effect = side_effect_year

    mock_current_year = 2023

    with patch("ynamazon.amazon_transactions.date", autospec=True) as mock_date:
        mock_date.today.return_value.year = mock_current_year
        result = _fetch_amazon_order_history(session=mock_session)

    assert len(result) == 1
    assert result[0].order_number == "456"
    mock_amazon_orders.return_value.get_order_history.assert_called_once_with(
        year=mock_current_year
    )


def test_fetch_amazon_order_history_unauthenticated_session():
    session = MagicMock(spec=AmazonSession)
    session.is_authenticated = False

    with pytest.raises(ValueError, match="Session must be authenticated."):
        _fetch_amazon_order_history(session=session)


@patch(
    "ynamazon.amazon_transactions.AmazonOrders",
)
def test_fetch_amazon_order_history_several_items(
    mock_amazon_orders: "AmazonOrders",
    mock_amazon_many_items,
    mock_session,
    mock_settings,
):
    patch("ynamazon.settings.settings", mock_settings)
    mock_amazon_orders.return_value.get_order_history.return_value = [
        mock_amazon_many_items
    ]

    result = _fetch_amazon_order_history(session=mock_session, years=[2023])

    assert len(result) == 1
    assert len(result[0].items) == 5
    assert result[0].order_number == "567"
