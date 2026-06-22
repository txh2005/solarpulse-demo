from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from .services import detect_anomaly


class AnomalyRuleTests(TestCase):
    def test_night_and_single_point_do_not_trigger(self):
        data = [
            {"time": "00:00", "predicted_power_mw": 0, "actual_power_mw": 0, "ghi_wm2": 0},
            {"time": "12:00", "predicted_power_mw": 40, "actual_power_mw": 25, "ghi_wm2": 900},
            {"time": "13:00", "predicted_power_mw": 42, "actual_power_mw": 41, "ghi_wm2": 920},
        ]
        self.assertFalse(detect_anomaly(data)["has_anomaly"])

    def test_low_ghi_suppresses_device_alarm(self):
        data = [
            {"time": "14:00", "predicted_power_mw": 40, "actual_power_mw": 18, "ghi_wm2": 180},
            {"time": "15:00", "predicted_power_mw": 35, "actual_power_mw": 16, "ghi_wm2": 160},
        ]
        self.assertFalse(detect_anomaly(data)["has_anomaly"])

    def test_continuous_high_ghi_deviation_triggers(self):
        data = [
            {"time": "14:00", "predicted_power_mw": 43, "actual_power_mw": 26.5, "ghi_wm2": 760},
            {"time": "15:00", "predicted_power_mw": 36, "actual_power_mw": 23.8, "ghi_wm2": 680},
        ]
        result = detect_anomaly(data)
        self.assertTrue(result["has_anomaly"])
        self.assertEqual(result["likely_cause"], "LOCAL_EQUIPMENT_OR_SHADING")


class ApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)

    def setUp(self):
        self.client = APIClient()

    def test_metrics_and_curve(self):
        metrics = self.client.get("/api/metrics/")
        curve = self.client.get("/api/power-curve/")
        self.assertEqual(metrics.status_code, 200)
        self.assertEqual(metrics.data["active_alerts"], 1)
        self.assertEqual(curve.status_code, 200)
        self.assertEqual(len(curve.data), 24)
        self.assertEqual(curve.data[0]["predicted_power_mw"], 0)

    @patch("monitoring.views.llm_enabled", return_value=False)
    def test_assistant_rule_reply(self, _enabled):
        response = self.client.post("/api/assistant/", {"message": "分析今日发电异常"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("14:00", response.data["reply"])
        self.assertEqual(response.data["mode"], "rule")

    @patch("monitoring.views.call_llm", return_value="这是来自真实模型的诊断回复。")
    @patch("monitoring.views.llm_enabled", return_value=True)
    def test_assistant_llm_mode(self, _enabled, _call_llm):
        response = self.client.post(
            "/api/assistant/",
            {
                "message": "分析今日发电异常",
                "history": [{"role": "assistant", "content": "你好"}, {"role": "user", "content": "先看异常"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["mode"], "llm")
        self.assertIn("真实模型", response.data["reply"])
