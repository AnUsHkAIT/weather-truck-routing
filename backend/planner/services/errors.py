class TripPlannerError(Exception):
    """Base error. Carries the HTTP status the API should return."""
    status_code = 400


class GeocodingError(TripPlannerError):
    status_code = 400      # user typed an address we can't find


class RoutingError(TripPlannerError):
    status_code = 400      # no drivable route between the points


class UpstreamError(TripPlannerError):
    status_code = 502      # Mapbox / weather API is down or failed