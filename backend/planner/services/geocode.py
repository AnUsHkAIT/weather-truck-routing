import requests
from django.conf import settings

from .errors import GeocodingError, UpstreamError

GEOCODE_URL = "https://api.mapbox.com/search/geocode/v6/forward"


def geocode(query):
    """Turn 'Dallas, TX' into {'lat', 'lon', 'label'}."""
    query = (query or "").strip()
    if not query:
        raise GeocodingError("Address is required.")
    if not settings.MAPBOX_TOKEN:
        raise UpstreamError("MAPBOX_TOKEN is not configured on the server.")

    params = {
        "q": query,
        "limit": 1,
        "country": "us",          # the risk rules use mph/inches, so US trips
        "access_token": settings.MAPBOX_TOKEN,
    }
    try:
        resp = requests.get(GEOCODE_URL, params=params, timeout=15)
    except requests.RequestException as exc:
        raise UpstreamError("Geocoding service is unreachable.") from exc

    if resp.status_code != 200:
        raise UpstreamError(f"Geocoding service error ({resp.status_code}).")

    features = resp.json().get("features", [])
    if not features:
        raise GeocodingError(f"Could not find a location for '{query}'.")

    feature = features[0]
    lon, lat = feature["geometry"]["coordinates"]   # Mapbox order is lon, lat
    props = feature.get("properties", {})
    return {
        "lat": lat,
        "lon": lon,
        "label": props.get("full_address") or props.get("name") or query,
    }