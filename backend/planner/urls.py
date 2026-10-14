
from django.urls import path
from . import views

urlpatterns = [
    path("ping/", views.ping),
    path("debug/routes/", views.debug_routes),
]
