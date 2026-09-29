import os

from motor.motor_asyncio import AsyncIOMotorClient

from store.core.config import settings


class MongoClient:
    def __init__(self) -> None:
        if os.getenv("MONGODB_MOCK", "false").lower() == "true":
            from mongomock_motor import AsyncMongoMockClient

            self.client = AsyncMongoMockClient(settings.DATABASE_URL, uuidRepresentation="standard")
        else:
            self.client = AsyncIOMotorClient(settings.DATABASE_URL, uuidRepresentation="standard")

    def get(self):
        return self.client


db_client = MongoClient()
