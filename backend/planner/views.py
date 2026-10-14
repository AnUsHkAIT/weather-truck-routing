from datetime import timedelta, timezone as dt_timezone

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.analysis import analyze_route
from .services.errors import TripPlannerError
from .services.geocode import geocode
from .services.routing import get_routes
from .services.sampling import sample_route
from .services.weather import fetch_hourly


@api_view(["GET"])
def ping(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def debug_routes(request):
    """Temporary: proves geocoding + routing work."""
    try:
        origin = geocode(request.query_params.get("origin"))
        destination = geocode(request.query_params.get("destination"))
        routes = get_routes(origin, destination)
    except TripPlannerError as exc:
        return Response({"error": str(exc)}, status=exc.status_code)

    return Response({
        "origin": origin,
        "destination": destination,
        "routes": [
            {
                "id": r["id"],
                "miles": round(r["distance_mi"], 1),
                "hours": round(r["duration_s"] / 3600, 2),
                "points": len(r["coords"]),
            }
            for r in routes
        ],
    })


@api_view(["GET"])
def debug_analysis(request):
    """Temporary: runs the full routing and weather-risk pipeline."""
    q = request.query_params

    try:
        origin = geocode(q.get("origin"))
        destination = geocode(q.get("destination"))
        load_lb = float(q.get("load", 40000))

        depart = (
            parse_datetime(q.get("departure", ""))
            or timezone.now() + timedelta(hours=1)
        )

        if depart.tzinfo is None:
            depart = depart.replace(tzinfo=dt_timezone.utc)

        depart = depart.astimezone(dt_timezone.utc)

        routes = get_routes(origin, destination)
        out = []

        for route in routes:
            checkpoints, miles = sample_route(
                route["coords"],
                route["duration_s"],
                depart,
            )

            arrival = depart + timedelta(seconds=route["duration_s"])

            hourly = fetch_hourly(
                [(cp["lat"], cp["lon"]) for cp in checkpoints],
                depart.date().isoformat(),
                arrival.date().isoformat(),
            )

            stats = analyze_route(
                checkpoints,
                miles,
                load_lb,
                hourly,
            )

            out.append({
                "id": route["id"],
                "miles": round(miles, 1),
                "hours": round(route["duration_s"] / 3600, 2),
                "checkpoints": len(checkpoints),
                **{key: round(value, 2) for key, value in stats.items()},
                "first_checkpoints": [
                    {
                        "mile": cp["mile"],
                        "eta": cp["eta"].isoformat(),
                        "wind": cp["wind_mph"],
                        "rain": cp["rain_in_hr"],
                        "snow": cp["snow_in_hr"],
                        "risk": cp["risk_label"],
                    }
                    for cp in checkpoints[:4]
                ],
            })

    except (TripPlannerError, ValueError) as exc:
        status = getattr(exc, "status_code", 400)
        return Response({"error": str(exc)}, status=status)

    return Response({
        "load_lb": load_lb,
        "departure": depart.isoformat(),
        "routes": out,
    })