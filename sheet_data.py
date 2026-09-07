import csv
import io
import logging
import os
import time
import urllib.request

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 5 * 60  # re-pull the sheet every 5 minutes


def make_csv_fetcher(env_var_name, label, required=True):
    """Returns a get_*() function that fetches + caches a published Google Sheet CSV.

    If required=True, a missing env var or a failed first fetch raises. If required=False,
    those cases just return an empty list (used for optional sheets like FAQs).
    """
    cache = {"data": None, "fetched_at": 0}

    def _fetch_csv(url):
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode("utf-8")

    def get_data():
        now = time.time()
        if cache["data"] is not None and now - cache["fetched_at"] < CACHE_TTL_SECONDS:
            return cache["data"]

        url = os.environ.get(env_var_name, "")
        if not url:
            if required:
                raise RuntimeError(f"{env_var_name} environment variable is not set")
            return []

        try:
            raw_csv = _fetch_csv(url)
            reader = csv.DictReader(io.StringIO(raw_csv))
            rows = [row for row in reader if any(value.strip() for value in row.values() if value)]
            cache["data"] = rows
            cache["fetched_at"] = now
            logger.info("Refreshed %s: %d rows", label, len(rows))
            return rows
        except Exception:
            if cache["data"] is not None:
                logger.exception("Failed to refresh %s, serving stale cache", label)
                return cache["data"]
            if required:
                raise
            logger.exception("Failed to fetch %s", label)
            return []

    return get_data
