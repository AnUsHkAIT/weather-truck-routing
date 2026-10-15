from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def home(request):
    return JsonResponse({
        "status": "ok",
        "message": "Weather Truck Routing API is running"
    })


def ping(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", home, name="home"),
    path("api/ping/", ping, name="ping"),
    path("admin/", admin.site.urls),
    path("api/", include("planner.urls")),
]
