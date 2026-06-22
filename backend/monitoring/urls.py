from django.urls import path

from . import views

urlpatterns = [
    path("metrics/", views.metrics),
    path("power-curve/", views.power_curve),
    path("anomalies/", views.anomalies),
    path("assistant/", views.assistant),
    path("ai-advice/", views.ai_advice),
    path("sub-arrays/", views.sub_arrays),
]
