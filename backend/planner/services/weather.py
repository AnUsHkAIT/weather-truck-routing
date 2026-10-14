import hashlib
import json
from datetime import datetime, timezone

import requests
from django.core.cache import cache

from .errors import UpstreamError

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CHUNK = 50                 # locations per request
CACHE_SECONDS = 30 * 60    # forecasts change slowly, so 30 minutes is fine


def fetch_hourly(points, start_date, end_date):
    """Fetch hourly weather for many (lat, lon) points.

    Returns one dict per point, in the same order as `points`.
    Each dict has: time[], wind_speed_10m[] (mph), rain[] (in), snowfall[] (in).
    """
    results = []
    for i in range(0, len(points), CHUNK):
        chunk = points[i:i + CHUNK]
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
        # Stable cache key (Python's built-in hash() changes between runs)
        key = "wx:" + hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        data = cache.get(key)
        if data is None:
            data = _call_api(params)
            cache.set(key, data, CACHE_SECONDS)
        results.extend(data)
    return results


def _call_api(params):
    try:
        resp = requests.get(FORECAST_URL, params=params, timeout=25)
    except requests.RequestException as exc:
        raise UpstreamError("Weather service is unreachable.") from exc

    if resp.status_code != 200:
        try:
            reason = resp.json().get("reason", "")
        except ValueError:
            reason = ""
        raise UpstreamError(f"Weather service error ({resp.status_code}). {reason}".strip())

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