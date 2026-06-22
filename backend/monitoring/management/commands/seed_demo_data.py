import math
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from monitoring.models import AiAdvice, AnomalyEvent, PowerActual, PowerForecast, PowerStation, SubArray, WeatherData
from monitoring.services import build_advice_from_detection, build_curve_rows, detect_anomaly


class Command(BaseCommand):
    help = "Seed SolarPulse demo plant, 24h curve, anomaly event and AI advice."

    def handle(self, *args, **options):
        AiAdvice.objects.all().delete()
        AnomalyEvent.objects.all().delete()
        PowerActual.objects.all().delete()
        PowerForecast.objects.all().delete()
        WeatherData.objects.all().delete()
        SubArray.objects.all().delete()
        PowerStation.objects.all().delete()

        station = PowerStation.objects.create(
            name="SolarPulse Demo Plant",
            location="Mountain PV Zone A",
            capacity_mw=Decimal("50.00"),
            panel_count=50000,
        )
        sub_arrays = [
            SubArray.objects.create(
                station=station,
                name=f"Sub-array #{index}",
                capacity_mw=Decimal("10.00"),
                orientation="South-East" if index % 2 else "South-West",
                tilt_angle=Decimal("24.00") + Decimal(index),
                inverter_id=f"INV-00{index}",
                status="WARNING" if index == 5 else "NORMAL",
            )
            for index in range(1, 6)
        ]

        base = timezone.make_aware(datetime(2026, 6, 22, 0, 0, 0))
        for hour in range(24):
            record_time = base + timedelta(hours=hour)
            shape = 0 if hour < 6 or hour > 19 else math.sin(((hour - 6) / 13) * math.pi)
            predicted = max(0, 47.5 * (shape ** 1.12))
            ghi = int(max(0, 990 * (shape ** 1.05)))
            actual_factor = 0.965
            weather_status = "Sunny"
            cloud_cover = 8
            if hour in [14, 15]:
                actual_factor = 0.61 if hour == 14 else 0.66
                weather_status = "Sunny"
                cloud_cover = 18
            actual = predicted * actual_factor
            pr = 0 if predicted == 0 else min(86, (actual / predicted) * 85)

            PowerForecast.objects.create(
                station=station,
                forecast_time=record_time,
                predicted_power_mw=Decimal(str(round(predicted, 2))),
                predicted_energy_mwh=Decimal(str(round(predicted, 2))),
                forecast_model="PF-24H-RULE",
            )
            PowerActual.objects.create(
                station=station,
                sub_array=None,
                record_time=record_time,
                actual_power_mw=Decimal(str(round(actual, 2))),
                energy_mwh=Decimal(str(round(actual, 2))),
                pr_value=Decimal(str(round(pr, 2))),
                data_source="SCADA_SIM",
            )
            if hour in [14, 15]:
                PowerActual.objects.create(
                    station=station,
                    sub_array=sub_arrays[-1],
                    record_time=record_time,
                    actual_power_mw=Decimal(str(round(actual / 5, 2))),
                    energy_mwh=Decimal(str(round(actual / 5, 2))),
                    pr_value=Decimal(str(round(pr, 2))),
                    data_source="INV-005_SIM",
                )
            WeatherData.objects.create(
                station=station,
                record_time=record_time,
                weather_status=weather_status,
                ghi_wm2=ghi,
                temperature_c=Decimal("25.40") + Decimal(str(round(shape * 8, 2))),
                wind_speed_ms=Decimal("2.80"),
                cloud_cover_percent=cloud_cover,
            )

        curve = build_curve_rows(
            PowerForecast.objects.filter(station=station),
            PowerActual.objects.filter(station=station, sub_array__isnull=True),
            WeatherData.objects.filter(station=station),
        )
        detection = detect_anomaly(curve)
        advice = build_advice_from_detection(detection)
        if detection.get("has_anomaly"):
            event = AnomalyEvent.objects.create(
                station=station,
                sub_array=sub_arrays[-1],
                start_time=base + timedelta(hours=14),
                end_time=base + timedelta(hours=15),
                anomaly_type="POWER_DEVIATION",
                severity="MEDIUM",
                deviation_percent=Decimal(str(detection["max_deviation_percent"])),
                estimated_loss_mwh=Decimal(str(detection["estimated_loss_mwh"])),
                status="OPEN",
                description="实际功率显著低于预测功率。",
            )
            AiAdvice.objects.create(
                anomaly_event=event,
                advice_text=advice["summary"],
                recommended_action="; ".join(advice["actions"]),
                priority=advice["priority"],
            )
        self.stdout.write(self.style.SUCCESS("SolarPulse demo data seeded."))
