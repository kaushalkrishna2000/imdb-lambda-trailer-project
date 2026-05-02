import requests

from common.config import WORLDTIME_API_URL


def _day_of_week_name(day_of_week: int) -> str:
    day_mapping = dict(zip(range(1, 8), ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]))
    return day_mapping[day_of_week]


def _parse_date_part(date_string: str, mode: str) -> int:
    date_part = date_string.split("T")[0]
    index = {"year": 0, "month": 1, "date": 2}[mode]
    return int(date_part.split("-")[index])


def generate_time_data() -> dict:
    response = requests.get(WORLDTIME_API_URL)
    data = response.json()

    return {
        "timestamp": data["datetime"],
        "day_of_week_number": data["day_of_week"],
        "day_of_week": _day_of_week_name(data["day_of_week"]),
        "week_number": data["week_number"],
        "datetime_date": _parse_date_part(data["datetime"], "date"),
        "datetime_month": _parse_date_part(data["datetime"], "month"),
        "datetime_year": _parse_date_part(data["datetime"], "year"),
    }
