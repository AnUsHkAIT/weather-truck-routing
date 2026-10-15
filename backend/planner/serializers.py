from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

MAX_DAYS_AHEAD = 13       # forecast covers ~16 days; we need 48h of heatmap too
MAX_LOAD_LB = 150_000


class PlanRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=200)
    destination = serializers.CharField(max_length=200)
    departure = serializers.DateTimeField()
    load_lb = serializers.FloatField(min_value=0, max_value=MAX_LOAD_LB)

    def validate_departure(self, value):
        now = timezone.now()
        if value < now - timedelta(days=1):
            raise serializers.ValidationError("Departure can't be more than 24 hours in the past.")
        if value > now + timedelta(days=MAX_DAYS_AHEAD):
            raise serializers.ValidationError(
                f"Departure must be within the next {MAX_DAYS_AHEAD} days (weather forecast limit)."
            )
        return value

    def validate(self, data):
        if data["origin"].strip().lower() == data["destination"].strip().lower():
            raise serializers.ValidationError("Origin and destination must be different.")
        return data