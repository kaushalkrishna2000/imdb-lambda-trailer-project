"""Local development script that performs one scrape-and-insert cycle into the MongoDB daily collection.

Mirrors the logic of ``daily/lambda_function.py`` but uses ``insert_one`` instead of
``find_one_and_replace``, so repeated runs accumulate multiple documents rather than
overwriting the day's record. Intended for verifying IMDb selector validity and
MongoDB connectivity without deploying to AWS Lambda.

Usage:
    export MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net"
    python -m default.main_script
"""

import logging

from common.config import DAILY_COLLECTION
from common.date_time_extractor import generate_time_data
from common.db import get_db
from common.trailer_scraper import generate_data

logger = logging.getLogger()
logger.setLevel("INFO")

db = get_db()
collection = db.get_collection(DAILY_COLLECTION)

imdb_trailer_metadata = generate_data()
date_time_metadata = generate_time_data()

logger.info(f"Imdb trailer metadata: {imdb_trailer_metadata}")
logger.info(f"Date time metadata: {date_time_metadata}")

imdb_mongo_metadata = {
    "timestamp": date_time_metadata["timestamp"],
    "day_of_week": date_time_metadata["day_of_week"],
    "day_of_week_number": date_time_metadata["day_of_week_number"],
    "week_number": date_time_metadata["week_number"],
    "date": date_time_metadata["datetime_date"],
    "month": date_time_metadata["datetime_month"],
    "year": date_time_metadata["datetime_year"],
    "details": imdb_trailer_metadata,
}

logger.info(f"Imdb mongo metadata: {imdb_mongo_metadata}")

resp = collection.insert_one(imdb_mongo_metadata)
logger.info(f"Inserted into MongoDB: {resp.inserted_id}")
