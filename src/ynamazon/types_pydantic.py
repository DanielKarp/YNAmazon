from typing import Annotated, Any

from amazonorders.entity.item import Item
from amazonorders.entity.seller import Seller
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class _AmazonItem:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: "GetCoreSchemaHandler"
    ) -> CoreSchema:
        return core_schema.is_instance_schema(Item)


AmazonItemType = Annotated[Item, _AmazonItem]


class _AmazonSeller:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: "GetCoreSchemaHandler"
    ) -> CoreSchema:
        return core_schema.is_instance_schema(Seller)


AmazonSellerType = Annotated[Seller, _AmazonSeller]

__all__ = ["AmazonItemType", "AmazonSellerType"]
