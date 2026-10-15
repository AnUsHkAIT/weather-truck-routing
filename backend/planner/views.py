from datetime import timezone as dt_timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PlanRequestSerializer
from .services.errors import TripPlannerError
from .services.plan import plan_trip


@api_view(["GET"])
def ping(request):
    return Response({"status": "ok"})


class PlanView(APIView):
    """POST /api/plan/ : plan 3 routes, score weather risk, recommend one."""

    def post(self, request):
        serializer = PlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        depart_utc = data["departure"].astimezone(dt_timezone.utc)

        try:
            result = plan_trip(data["origin"], data["destination"], depart_utc, data["load_lb"])
        except TripPlannerError as exc:
            return Response({"error": str(exc)}, status=exc.status_code)
        return Response(result)