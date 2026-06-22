from django.db import models


class PowerStation(models.Model):
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=160)
    capacity_mw = models.DecimalField(max_digits=8, decimal_places=2)
    panel_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SubArray(models.Model):
    station = models.ForeignKey(PowerStation, on_delete=models.CASCADE, related_name="sub_arrays")
    name = models.CharField(max_length=80)
    capacity_mw = models.DecimalField(max_digits=8, decimal_places=2)
    orientation = models.CharField(max_length=40)
    tilt_angle = models.DecimalField(max_digits=5, decimal_places=2)
    inverter_id = models.CharField(max_length=40)
    status = models.CharField(max_length=40, default="NORMAL")

    def __str__(self):
        return f"{self.station.name} / {self.name}"


class WeatherData(models.Model):
    station = models.ForeignKey(PowerStation, on_delete=models.CASCADE, related_name="weather_records")
    record_time = models.DateTimeField()
    weather_status = models.CharField(max_length=40)
    ghi_wm2 = models.PositiveIntegerField(default=0)
    temperature_c = models.DecimalField(max_digits=5, decimal_places=2)
    wind_speed_ms = models.DecimalField(max_digits=5, decimal_places=2)
    cloud_cover_percent = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["record_time"]


class PowerForecast(models.Model):
    station = models.ForeignKey(PowerStation, on_delete=models.CASCADE, related_name="forecasts")
    forecast_time = models.DateTimeField()
    predicted_power_mw = models.DecimalField(max_digits=8, decimal_places=2)
    predicted_energy_mwh = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    forecast_model = models.CharField(max_length=80, default="PF-24H-RULE")

    class Meta:
        ordering = ["forecast_time"]


class PowerActual(models.Model):
    station = models.ForeignKey(PowerStation, on_delete=models.CASCADE, related_name="actuals")
    sub_array = models.ForeignKey(SubArray, null=True, blank=True, on_delete=models.SET_NULL, related_name="actuals")
    record_time = models.DateTimeField()
    actual_power_mw = models.DecimalField(max_digits=8, decimal_places=2)
    energy_mwh = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    pr_value = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    data_source = models.CharField(max_length=80, default="SCADA_SIM")

    class Meta:
        ordering = ["record_time"]


class AnomalyEvent(models.Model):
    station = models.ForeignKey(PowerStation, on_delete=models.CASCADE, related_name="anomalies")
    sub_array = models.ForeignKey(SubArray, null=True, blank=True, on_delete=models.SET_NULL, related_name="anomalies")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    anomaly_type = models.CharField(max_length=60)
    severity = models.CharField(max_length=30)
    deviation_percent = models.DecimalField(max_digits=6, decimal_places=2)
    estimated_loss_mwh = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=30, default="OPEN")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_time"]


class AiAdvice(models.Model):
    anomaly_event = models.ForeignKey(AnomalyEvent, on_delete=models.CASCADE, related_name="advices")
    advice_text = models.TextField()
    recommended_action = models.TextField()
    priority = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
