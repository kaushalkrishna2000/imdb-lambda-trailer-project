"""MongoDB connection helper used by all Lambda functions and the local dev script."""

import os

from pymongo import MongoClient

from common.config import DB_NAME


def get_db():
    """Return a handle to the ``imdb_trailer`` MongoDB database.

    Reads the ``MONGO_URI`` environment variable to build the connection.
    The variable must be set before calling this function (via Lambda
    environment variables or a local ``export``/``set`` command).

    Returns:
        pymongo.database.Database: The ``imdb_trailer`` database object.

    Raises:
        pymongo.errors.ConfigurationError: If ``MONGO_URI`` is missing or malformed.
        pymongo.errors.ServerSelectionTimeoutError: If the Atlas cluster is unreachable.
    """
    client = MongoClient(os.getenv("MONGO_URI"))
    return client.get_database(DB_NAME)
