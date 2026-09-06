import os
import time
import csv
import io
import logging
import urllib.request

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 5 * 60  # re-pull the sheet every 5 minutes

_cache = {"data": None, "fetched_at": 0}


def _fetch_csv():
    sheet_url = os.environ.get("SHEET_CSV_URL", "")
    if not sheet_url:
        raise RuntimeError("SHEET_CSV_URL environment variable is not set")
    with urllib.request.urlopen(sheet_url, timeout=10) as response:
        return response.read().decode("utf-8")


def get_restaurant_data():
    now = time.time()
    if _cache["data"] is not None and now - _cache["fetched_at"] < CACHE_TTL_SECONDS:
        return _cache["data"]

    try:
        raw_csv = _fetch_csv()
        reader = csv.DictReader(io.StringIO(raw_csv))
        rows = [row for row in reader if any(value.strip() for value in row.values() if value)]
        _cache["data"] = rows
        _cache["fetched_at"] = now
        logger.info("Refreshed restaurant data: %d rows", len(rows))
        return rows
    except Exception:
        if _cache["data"] is not None:
            logger.exception("Failed to refresh restaurant data, serving stale cache")
            return _cache["data"]
        raise
