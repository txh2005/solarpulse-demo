from rest_framework import serializers

from .models import AiAdvice, AnomalyEvent


class AiAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiAdvice
        fields = ["advice_text", "recommended_action", "priority", "created_at"]


class AnomalyEventSerializer(serializers.ModelSerializer):
    advice_text = serializers.SerializerMethodField()
    recommended_action = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()

    class Meta:
        model = AnomalyEvent
        fields = [
            "start_time",
            "end_time",
            "anomaly_type",
            "severity",
            "deviation_percent",
            "estimated_loss_mwh",
            "description",
            "advice_text",
            "recommended_action",
            "priority",
        ]

    def get_latest_advice(self, obj):
        return obj.advices.order_by("-created_at").first()

    def get_advice_text(self, obj):
        advice = self.get_latest_advice(obj)
        return advice.advice_text if advice else ""

    def get_recommended_action(self, obj):
        advice = self.get_latest_advice(obj)
        return advice.recommended_action if advice else ""

    def get_priority(self, obj):
        advice = self.get_latest_advice(obj)
        return advice.priority if advice else obj.severity
