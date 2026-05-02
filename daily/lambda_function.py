"""AWS Lambda handler that scrapes IMDb trailers and upserts one document per calendar day into MongoDB."""

import json
import logging

from common.config import DAILY_COLLECTION
from common.date_time_extractor import generate_time_data
from common.db import get_db
from common.trailer_scraper import generate_data

logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    """Scrape IMDb trailers and upsert the result as a daily snapshot in MongoDB.

    Fetches the current IST timestamp from WorldTimeAPI, scrapes visible trailer
    titles from the IMDb trailers page, then upserts a single document into the
    ``daily`` collection keyed by ``(date, month, year)``. Re-running on the same
    calendar day overwrites the existing document (idempotent via
    ``find_one_and_replace`` with ``upsert=True``).

    Args:
        event (dict): Lambda invocation payload (unused — function is schedule-triggered).
        context (LambdaContext): Lambda runtime context (unused).

    Returns:
        dict: HTTP-style response with ``statusCode`` 200 and a success message body.

    Side effects:
        - Upserts one document into the MongoDB ``daily`` collection.
        - Logs scrape metadata and the MongoDB response at INFO level.
    """
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

    resp = collection.find_one_and_replace(
        {
            "date": date_time_metadata["datetime_date"],
            "month": date_time_metadata["datetime_month"],
            "year": date_time_metadata["datetime_year"],
        },
        imdb_mongo_metadata,
        upsert=True,
    )
    logger.info(f"MongoDB upsert response: {resp}")

    return {
        "statusCode": 200,
        "body": json.dumps("Lambda Execution Successful!"),
    }
