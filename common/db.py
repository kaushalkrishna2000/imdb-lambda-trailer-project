import os

from pymongo import MongoClient

from common.config import DB_NAME


def get_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    return client.get_database(DB_NAME)
