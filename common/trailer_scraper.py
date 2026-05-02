"""IMDb trailers page scraper that returns a list of currently trending movie/show titles."""

import datetime
import logging

import pytz
import requests
from bs4 import BeautifulSoup

from common.config import IMDB_TRAILERS_URL

logger = logging.getLogger()

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 OPR/102.0.0.0"
    )
}


def generate_data() -> list[str]:
    """Scrape the IMDb trailers page and return the list of visible trailer titles.

    Makes a single HTTP GET request to the IMDb trailers page using a desktop
    Chrome User-Agent to avoid bot detection. Parses the response HTML with
    BeautifulSoup/lxml and extracts the text of every ``ipc-poster-card__title``
    anchor found inside an ``ipc-poster-card`` container.

    Side effects:
        Logs the HTTP response status and the IST scrape timestamp at INFO level.

    Returns:
        list[str]: Ordered list of trailer title strings as they appear on the page.
            Returns an empty list if the page contains no matching elements.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails (timeout,
            connection error, etc.).
    """
    r = requests.get(IMDB_TRAILERS_URL, headers=_HEADERS)
    logger.info(f"{r}, {r.status_code}, {r.reason}")

    soup = BeautifulSoup(r.content, "lxml")

    ist = pytz.timezone("Asia/Kolkata")
    record_time = str(datetime.datetime.now(tz=ist))
    logger.info(f"Scrape time (IST): {record_time}")

    titles = [
        ele.find("a", {"class": "ipc-poster-card__title"}).text
        for ele in soup.find_all("div", {"class": "ipc-poster-card"})
    ]
    return titles
