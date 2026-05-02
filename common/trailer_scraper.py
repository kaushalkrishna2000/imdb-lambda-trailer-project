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
