import json
import logging

from common.config import DAILY_COLLECTION, WEEKLY_COLLECTION
from common.date_time_extractor import generate_time_data
from common.db import get_db

logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    db = get_db()
    collection_daily = db.get_collection(DAILY_COLLECTION)
    collection_weekly = db.get_collection(WEEKLY_COLLECTION)

    date_time_metadata = generate_time_data()
    logger.info(f"Date time metadata: {date_time_metadata}")

    week_number = date_time_metadata["week_number"]

    prev_week_data = collection_daily.find({"week_number": week_number})

    weekly_dict = {}
    weekly_date_range = []

    for data_point in prev_week_data:
        logger.info(data_point)
        weekly_date_range.append(data_point["date"])
        for title in data_point["details"]:
            weekly_dict[title] = weekly_dict.get(title, 0) + 1

    imdb_mongo_metadata = {
        "record_time": date_time_metadata["timestamp"],
        "week_number": week_number,
        "week_range": weekly_date_range,
        "month": date_time_metadata["datetime_month"],
        "year": date_time_metadata["datetime_year"],
        "details": weekly_dict,
    }

    logger.info(f"Imdb mongo metadata: {imdb_mongo_metadata}")

    resp = collection_weekly.find_one_and_replace(
        {"week_number": week_number}, imdb_mongo_metadata, upsert=True
    )
    logger.info(f"MongoDB upsert response: {resp}")

    return {
        "statusCode": 200,
        "body": json.dumps("Lambda Execution Successful!"),
    }
