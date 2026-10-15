import hashlib
import json
import time
from datetime import datetime, timezone

import requests
from django.core.cache import cache

from .errors import UpstreamError

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CHUNK = 40                 # locations per request
CACHE_SECONDS = 60 * 60    # forecasts change slowly, so 1 hour is fine
MAX_ATTEMPTS = 6           # tries per request when the API is busy
RETRY_STATUSES = {429, 500, 502, 503, 504}
PAUSE_BETWEEN_CHUNKS = 0.5


def fetch_hourly(points, start_date, end_date):
    """Fetch hourly weather for many (lat, lon) points, in the same order.

    Chunks are requested one at a time (the free API rejects bursts).
    Busy responses are retried with a growing wait. Results are cached.
    """
    results = []
    for i in range(0, len(points), CHUNK):
        results.extend(_fetch_chunk(points[i:i + CHUNK], start_date, end_date))
    return results


def _fetch_chunk(chunk, start_date, end_date):
    params = {
        "latitude": ",".join(f"{lat:.3f}" for lat, _ in chunk),
        "longitude": ",".join(f"{lon:.3f}" for _, lon in chunk),
        "hourly": "wind_speed_10m,rain,snowfall",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "UTC",
        "start_date": start_date,
        "end_date": end_date,
    }
    key = "wx:" + hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
    data = cache.get(key)
    if data is None:
        data = _call_api(params)
        cache.set(key, data, CACHE_SECONDS)
        time.sleep(PAUSE_BETWEEN_CHUNKS)
    return data


def _call_api(params):
    for attempt in range(MAX_ATTEMPTS):
        try:
            resp = requests.get(FORECAST_URL, params=params, timeout=30)
        except requests.RequestException as exc:
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise UpstreamError("Weather service is unreachable.") from exc

        # Busy / overloaded: wait 2s, 4s, 6s, 8s, 10s then try again
        if resp.status_code in RETRY_STATUSES and attempt < MAX_ATTEMPTS - 1:
            time.sleep(2 * (attempt + 1))
            continue

        if resp.status_code != 200:
            try:
                reason = resp.json().get("reason", "")
            except ValueError:
                reason = ""
            raise UpstreamError(
                f"Weather service error ({resp.status_code}). {reason}".strip()
            )

        data = resp.json()
        # One location returns a dict, several return a list: always use a list
        data = data if isinstance(data, list) else [data]
        return [item["hourly"] for item in data]


def value_at(hourly, eta_utc):
    """Return (wind_mph, rain_in_hr, snow_in_hr) for the hour closest to eta_utc."""
    first = datetime.fromisoformat(hourly["time"][0]).replace(tzinfo=timezone.utc)
    idx = round((eta_utc - first).total_seconds() / 3600)
    idx = max(0, min(idx, len(hourly["time"]) - 1))   # clamp to the data we have
    return (hourly["wind_speed_10m"][idx],
            hourly["rain"][idx],
            hourly["snowfall"][idx])