from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.errors import TripPlannerError
from .services.geocode import geocode
from .services.routing import get_routes


@api_view(["GET"])
def ping(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def debug_routes(request):
    """Temporary: proves geocoding + routing work. Replaced by /api/plan/ later."""
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