"""IST date/time helper that fetches the current time from WorldTimeAPI and returns structured calendar metadata."""

import requests

from common.config import WORLDTIME_API_URL


def _day_of_week_name(day_of_week: int) -> str:
    """Convert a WorldTimeAPI day-of-week integer to its English name.

    WorldTimeAPI uses 1 = Monday through 7 = Sunday (ISO 8601 weekday numbering).

    Args:
        day_of_week: Integer day-of-week value from the WorldTimeAPI response (1–7).

    Returns:
        str: Full English day name, e.g. ``"Monday"``, ``"Sunday"``.
    """
    day_mapping = dict(zip(range(1, 8), ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]))
    return day_mapping[day_of_week]


def _parse_date_part(date_string: str, mode: str) -> int:
    """Extract a single calendar component (year, month, or date) from an ISO 8601 datetime string.

    Args:
        date_string: ISO 8601 datetime string, e.g. ``"2026-05-02T23:55:00.000+05:30"``.
        mode: Which part to extract — one of ``"year"``, ``"month"``, or ``"date"``.

    Returns:
        int: The requested calendar component as an integer.
    """
    date_part = date_string.split("T")[0]
    index = {"year": 0, "month": 1, "date": 2}[mode]
    return int(date_part.split("-")[index])


def generate_time_data() -> dict:
    """Fetch the current IST date and time from WorldTimeAPI and return structured calendar metadata.

    Makes a single HTTP GET request to the WorldTimeAPI ``Asia/Kolkata`` endpoint
    and normalises the response into a flat dictionary used by all three Lambda
    functions when building MongoDB documents.

    Returns:
        dict: A dictionary with the following keys:

            - ``timestamp`` (str): Full ISO 8601 datetime string from WorldTimeAPI.
            - ``day_of_week_number`` (int): Day of week as an integer (1 = Monday, 7 = Sunday).
            - ``day_of_week`` (str): Full English day name, e.g. ``"Saturday"``.
            - ``week_number`` (int): ISO 8601 week number (1–53).
            - ``datetime_date`` (int): Day of month (1–31).
            - ``datetime_month`` (int): Month number (1–12).
            - ``datetime_year`` (int): Four-digit year.

    Raises:
        requests.exceptions.RequestException: If the WorldTimeAPI request fails.
        KeyError: If the WorldTimeAPI response is missing expected fields.
    """
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
