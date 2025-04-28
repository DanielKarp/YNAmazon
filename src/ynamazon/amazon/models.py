# pyright: strict
import abc
import datetime as dt
import uuid
from decimal import Decimal
from typing import Annotated, Any, Union

from amazonorders.session import AmazonSession
from amazonorders.transactions import AmazonTransactions
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from ynamazon.amazon_transactions import AmazonConfig
from ynamazon.settings import get_settings
from ynamazon.types_pydantic import AmazonSellerType
from ynamazon.utilities import MISSING, Missing, getattr_path
from ynamazon.utilities.bases import SimpleDict


class BaseClone(BaseModel, abc.ABC):
    model_config = ConfigDict(from_attributes=True)


class Entity(BaseClone, abc.ABC):
    pass


class Item(Entity):
    title: str
    link: HttpUrl
    price: Union[Decimal, None] = None
    seller: Union[AmazonSellerType, None] = None
    condition: Union[str, None] = None
    return_eligible_date: Union[dt.date, None] = None
    image_link: Union[HttpUrl, None] = None
    quantity: Union[int, None] = None

    def __str__(self) -> str:
        if get_settings().ynab_use_markdown:
            return f"[{self.title}]({self.link})"
        return self.title

    def truncated(self, max_length: int) -> str:
        """Returns a truncated version of the title."""
        if len(self.title) > max_length:
            return f"{self.title[: max_length - 3]}..."
        return self.title


class Address(BaseModel):
    value: str

    @model_validator(mode="before")
    @classmethod
    def address_from_str(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"value": data}
        return data


class Recipient(Entity):
    name: str
    address: Union[Address, None] = Field(
        repr=False, default=None, description="not parsed properly, don't use"
    )


class Shipment(Entity):
    items: list[Item]
    delivery_status: Union[str, None] = None
    tracking_link: Union[HttpUrl, None] = None


class Order(Entity):
    """Pydantic wrapper around amazonorders.Order."""

    full_details: bool = False
    shipments: list[Shipment]
    items: list[Item]
    order_number: str
    order_details_link: Union[HttpUrl, None] = None
    grand_total: Decimal
    order_placed_date: dt.date
    recipient: Union[Recipient, None] = None
    payment_method: Union[str, None] = None
    payment_method_last_4: Union[str, None] = None
    total_before_tax: Union[Decimal, None] = None


class Orders(SimpleDict[str, Order]):
    @classmethod
    def get_order_history(
        cls,
        config: AmazonConfig,
        session: Union[AmazonSession, None] = None,
        years: Union[list[int], Union[int, None]] = None,
        *,
        debug: Union[bool, None] = None,
    ):
        from ynamazon.amazon_transactions import (
            _fetch_amazon_order_history,  # pyright: ignore[reportPrivateUsage]
        )

        debug = debug if debug is not None else config.debug
        if session is None:
            session = config.amazon_session(debug=debug)
        if isinstance(years, int):
            years = [years]
        raw_orders = _fetch_amazon_order_history(
            session=session, years=years, debug=debug, config=config.config
        )
        raw_orders_dict = {order.order_number: order for order in raw_orders}

        return cls.model_validate(raw_orders_dict)


class Transaction(Entity):
    completed_date: dt.date
    payment_method: str
    grand_total: Decimal
    is_refund: bool
    order_number: str
    order_details_link: HttpUrl
    seller_name: Annotated[str, Field(alias="seller")]
    order: Union[Order, None] = None

    def match_order(self, orders: Orders) -> None:
        """Matches the transaction with the order."""
        self.order = orders.get(self.order_number)

    def getattr_path(
        self,
        attr_path: str,
        *,
        separator: str = "__",
        default: Union[Any, Missing] = MISSING,
    ) -> Any:
        return getattr_path(self, attr_path, separator=separator, default=default)


class Transactions(SimpleDict[str, Transaction]):
    """Pydantic wrapper around a list of transactions."""

    @model_validator(mode="before")
    @classmethod
    def add_uuid(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {str(uuid.uuid4())[-4:]: value for value in data}  # pyright: ignore[reportUnknownVariableType]

        return data  # pyright: ignore[reportUnknownVariableType]

    @classmethod
    def get_transactions(
        cls,
        config: AmazonConfig,
        amazon_session: AmazonSession,
        transaction_days: int = 31,
        *,
        debug: bool = False,
    ):
        if not amazon_session.is_authenticated:
            raise ValueError("Amazon session is not authenticated.")

        raw_transactions = AmazonTransactions(
            amazon_session=amazon_session, debug=debug, config=config.config
        ).get_transactions(days=transaction_days)

        return cls.model_validate(raw_transactions)

    def match_orders(self, orders: Orders) -> None:
        """Matches the transactions with the orders."""
        for _, transaction in self.items():
            transaction.match_order(orders)
