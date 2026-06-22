from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .llm_gateway import build_llm_messages, build_operations_context, call_llm, llm_enabled
from .models import AnomalyEvent, PowerActual, PowerForecast, PowerStation, SubArray, WeatherData
from .serializers import AnomalyEventSerializer
from .services import assistant_reply, build_advice_from_detection, build_curve_rows, detect_anomaly


def get_station():
    return PowerStation.objects.order_by("id").first()


def build_metrics_payload(station):
    latest_actual = (
        PowerActual.objects.filter(station=station, sub_array__isnull=True, record_time__hour=14).order_by("-record_time").first()
        or PowerActual.objects.filter(station=station, sub_array__isnull=True).order_by("-record_time").first()
    )
    latest_weather = (
        WeatherData.objects.filter(station=station, record_time__hour=14).order_by("-record_time").first()
        or WeatherData.objects.filter(station=station).order_by("-record_time").first()
    )
    today_generation = sum(
        float(item.energy_mwh) for item in PowerActual.objects.filter(station=station, sub_array__isnull=True)
    )
    active_alerts = AnomalyEvent.objects.filter(station=station, status="OPEN").aggregate(count=Count("id"))["count"]

    return {
        "station_name": station.name,
        "location": station.location,
        "capacity_mw": float(station.capacity_mw),
        "current_power_mw": float(latest_actual.actual_power_mw) if latest_actual else 0,
        "today_generation_mwh": round(today_generation, 2),
        "pr_value": float(latest_actual.pr_value) if latest_actual else 0,
        "weather_status": latest_weather.weather_status if latest_weather else "未知",
        "ghi_wm2": latest_weather.ghi_wm2 if latest_weather else 0,
        "temperature_c": float(latest_weather.temperature_c) if latest_weather else 0,
        "active_alerts": active_alerts,
    }


@api_view(["GET"])
def metrics(request):
    station = get_station()
    if not station:
        return Response({"empty": True, "message": "暂无电站数据，请先运行 python manage.py seed_demo_data。"})
    return Response(build_metrics_payload(station))


@api_view(["GET"])
def power_curve(request):
    station = get_station()
    if not station:
        return Response([])

    forecasts = PowerForecast.objects.filter(station=station).order_by("forecast_time")
    actuals = PowerActual.objects.filter(station=station, sub_array__isnull=True).order_by("record_time")
    weather = WeatherData.objects.filter(station=station).order_by("record_time")
    return Response(build_curve_rows(forecasts, actuals, weather))


@api_view(["GET"])
def anomalies(request):
    station = get_station()
    if not station:
        return Response([])

    queryset = AnomalyEvent.objects.filter(station=station).prefetch_related("advices")
    return Response(AnomalyEventSerializer(queryset, many=True).data)


@api_view(["POST"])
def assistant(request):
    station = get_station()
    if not station:
        return Response({"reply": "当前没有电站数据，请先初始化演示数据。", "mode": "rule"})

    curve = build_curve_rows(
        PowerForecast.objects.filter(station=station).order_by("forecast_time"),
        PowerActual.objects.filter(station=station, sub_array__isnull=True).order_by("record_time"),
        WeatherData.objects.filter(station=station).order_by("record_time"),
    )
    detection = detect_anomaly(curve)
    message = request.data.get("message", "")
    history = request.data.get("history", [])
    metrics_payload = build_metrics_payload(station)
    anomaly_payload = AnomalyEventSerializer(
        AnomalyEvent.objects.filter(station=station).prefetch_related("advices"),
        many=True,
    ).data

    if llm_enabled():
        try:
            operations_context = build_operations_context(metrics_payload, detection, curve, anomaly_payload)
            llm_messages = build_llm_messages(message, history, operations_context)
            return Response({"reply": call_llm(llm_messages), "mode": "llm"})
        except Exception:
            pass

    return Response({"reply": assistant_reply(message, detection), "mode": "rule"})


@api_view(["GET"])
def ai_advice(request):
    station = get_station()
    if not station:
        return Response(build_advice_from_detection({"has_anomaly": False}))

    curve = build_curve_rows(
        PowerForecast.objects.filter(station=station).order_by("forecast_time"),
        PowerActual.objects.filter(station=station, sub_array__isnull=True).order_by("record_time"),
        WeatherData.objects.filter(station=station).order_by("record_time"),
    )
    detection = detect_anomaly(curve)
    advice = build_advice_from_detection(detection)
    return Response({**detection, **advice})


@api_view(["GET"])
def sub_arrays(request):
    station = get_station()
    if not station:
        return Response([])

    return Response(
        [
            {
                "id": item.id,
                "name": item.name,
                "capacity_mw": float(item.capacity_mw),
                "inverter_id": item.inverter_id,
                "orientation": item.orientation,
                "status": item.status,
            }
            for item in SubArray.objects.filter(station=station).order_by("id")
        ]
    )
