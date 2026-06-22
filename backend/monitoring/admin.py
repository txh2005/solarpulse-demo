from django.contrib import admin

from .models import AiAdvice, AnomalyEvent, PowerActual, PowerForecast, PowerStation, SubArray, WeatherData

admin.site.register(PowerStation)
admin.site.register(SubArray)
admin.site.register(WeatherData)
admin.site.register(PowerForecast)
admin.site.register(PowerActual)
admin.site.register(AnomalyEvent)
admin.site.register(AiAdvice)
