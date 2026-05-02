import json
import logging

from common.config import MONTHLY_COLLECTION, WEEKLY_COLLECTION
from common.date_time_extractor import generate_time_data
from common.db import get_db

logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    db = get_db()
    collection_weekly = db.get_collection(WEEKLY_COLLECTION)
    collection_monthly = db.get_collection(MONTHLY_COLLECTION)

    date_time_metadata = generate_time_data()
    logger.info(f"Date time metadata: {date_time_metadata}")

    month = date_time_metadata["datetime_month"]

    prev_month_data = collection_weekly.find({"month": month})

    monthly_dict = {}

    for data_point in prev_month_data:
        logger.info(data_point)
        for title, count in data_point["details"].items():
            monthly_dict[title] = monthly_dict.get(title, 0) + count

    imdb_mongo_metadata = {
        "record_time": date_time_metadata["timestamp"],
        "month": date_time_metadata["datetime_month"],
        "year": date_time_metadata["datetime_year"],
        "details": monthly_dict,
    }

    logger.info(f"Imdb mongo metadata: {imdb_mongo_metadata}")

    resp = collection_monthly.find_one_and_replace(
        {"month": month, "year": date_time_metadata["datetime_year"]},
        imdb_mongo_metadata,
        upsert=True,
    )
    logger.info(f"MongoDB upsert response: {resp}")

    return {
        "statusCode": 200,
        "body": json.dumps("Lambda Execution Successful!"),
    }
