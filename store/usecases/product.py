from datetime import datetime, timezone
import os
from decimal import Decimal
from typing import List
from uuid import UUID

import pymongo
from bson import Decimal128
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from store.core.exceptions import CreateException, NotFoundException
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut


def _db_decimal(value: Decimal):
    return Decimal128(str(value))


class ProductUsecase:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient = db_client.get()
        self.database: AsyncIOMotorDatabase = self.client.get_database()
        self.collection = self.database.get_collection("products")

    async def create(self, body: ProductIn) -> ProductOut:
        product_model = ProductModel(**body.model_dump())
        try:
            document = product_model.model_dump()
            document["id"] = str(document["id"])
            await self.collection.insert_one(document)
        except PyMongoError as exc:
            raise CreateException() from exc
        return ProductOut(**product_model.model_dump())

    async def get(self, id: UUID) -> ProductOut:
        result = await self.collection.find_one({"id": str(id)})
        if not result:
            raise NotFoundException(message=f"Product not found with filter: {id}")
        return ProductOut(**result)

    async def query(
        self,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> List[ProductOut]:
        filters = {}
        if min_price is not None:
            filters["price"] = {"$gt": _db_decimal(min_price)}
        if max_price is not None:
            filters.setdefault("price", {})["$lt"] = _db_decimal(max_price)

        cursor = self.collection.find({} if os.getenv("MONGODB_MOCK", "false").lower() == "true" else filters)
        products = []
        async for item in cursor:
            price = item["price"].to_decimal() if isinstance(item["price"], Decimal128) else item["price"]
            if min_price is not None and price <= min_price:
                continue
            if max_price is not None and price >= max_price:
                continue
            products.append(ProductOut(**item))
        return products

    async def update(self, id: UUID, body: ProductUpdate) -> ProductUpdateOut:
        changes = body.model_dump(exclude_none=True)
        if "price" in changes:
            changes["price"] = _db_decimal(changes["price"])
        changes.setdefault("updated_at", datetime.now(timezone.utc))
        result = await self.collection.find_one_and_update(
            filter={"id": str(id)},
            update={"$set": changes},
            return_document=pymongo.ReturnDocument.AFTER,
        )
        if not result:
            raise NotFoundException(message=f"Product not found with filter: {id}")
        return ProductUpdateOut(**result)

    async def delete(self, id: UUID) -> bool:
        product = await self.collection.find_one({"id": str(id)})
        if not product:
            raise NotFoundException(message=f"Product not found with filter: {id}")
        result = await self.collection.delete_one({"id": str(id)})
        return result.deleted_count > 0


product_usecase = ProductUsecase()
