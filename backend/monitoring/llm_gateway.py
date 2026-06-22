import json
import os
from urllib import error, request


def normalize_weather_text(value):
    weather_map = {
        "Sunny": "晴",
        "Cloudy": "多云",
        "Rainy": "雨",
        "Unknown": "未知",
    }
    return weather_map.get(value, value)


def llm_config():
    return {
        "api_key": os.getenv("LLM_API_KEY", "").strip(),
        "api_url": os.getenv("LLM_API_URL", "https://api.deepseek.com/chat/completions").strip(),
        "model": os.getenv("LLM_MODEL", "deepseek-chat").strip(),
        "timeout": int(os.getenv("LLM_TIMEOUT_SECONDS", "45")),
    }


def llm_enabled():
    config = llm_config()
    return bool(config["api_key"] and config["api_url"] and config["model"])


def normalize_history(history):
    normalized = []
    for item in history or []:
        role = (item or {}).get("role", "").strip()
        content = (item or {}).get("content", "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized[-8:]


def build_operations_context(metrics, detection, curve, anomalies):
    latest_points = []
    for point in (curve or [])[-6:]:
        latest_points.append(
            {
                "time": point.get("time"),
                "predicted_power_mw": point.get("predicted_power_mw"),
                "actual_power_mw": point.get("actual_power_mw"),
                "ghi_wm2": point.get("ghi_wm2"),
                "pr_value": point.get("pr_value"),
                "deviation_percent": point.get("deviation_percent"),
            }
        )

    anomaly_briefs = []
    for item in (anomalies or [])[:3]:
        anomaly_briefs.append(
            {
                "type": item.get("anomaly_type"),
                "severity": item.get("severity"),
                "start_time": item.get("start_time"),
                "end_time": item.get("end_time"),
                "deviation_percent": item.get("deviation_percent"),
                "description": item.get("description"),
            }
        )

    return {
        "station_metrics": {
            "station_name": metrics.get("station_name"),
            "location": metrics.get("location"),
            "capacity_mw": metrics.get("capacity_mw"),
            "current_power_mw": metrics.get("current_power_mw"),
            "today_generation_mwh": metrics.get("today_generation_mwh"),
            "pr_value": metrics.get("pr_value"),
            "weather_status": normalize_weather_text(metrics.get("weather_status")),
            "ghi_wm2": metrics.get("ghi_wm2"),
            "temperature_c": metrics.get("temperature_c"),
            "active_alerts": metrics.get("active_alerts"),
        },
        "detection": detection,
        "recent_curve_points": latest_points,
        "recent_anomalies": anomaly_briefs,
        "business_rules": [
            "夜间或预测功率为 0 时不触发异常。",
            "低 GHI + 低功率优先判断为天气原因。",
            "高 GHI + 连续低功率优先判断为设备、遮挡或局部故障。",
            "单个异常点不报警，连续两个点以上才触发。",
            "预测偏差不直接等于设备故障，需要结合天气和局部/全站范围判断。",
        ],
    }


def is_station_related_question(user_message):
    text = (user_message or "").lower()
    keywords = [
        "电站",
        "发电",
        "光伏",
        "pr",
        "ghi",
        "逆变器",
        "组串",
        "组件",
        "清洗",
        "告警",
        "异常",
        "功率",
        "预测",
        "辐照",
        "运维",
        "限电",
        "限发",
        "solar",
        "station",
        "inverter",
        "anomaly",
        "generation",
    ]
    return any(keyword in text for keyword in keywords)


def build_llm_messages(user_message, history, operations_context):
    if not is_station_related_question(user_message):
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个自然、礼貌、简洁的中文 AI 助手。"
                    "用户现在只是进行普通聊天或日常提问，请直接正常回答。"
                    "不要主动把话题引向光伏电站、发电、运维或专业分析，除非用户明确询问。"
                ),
            }
        ]
    else:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是 SolarPulse AI 运维助手。"
                    "当前用户的问题与光伏电站运维相关，请结合上下文进行专业回答。"
                    "优先给出结论，再给原因判断，再给排查建议。"
                    "如果数据不足，要明确指出缺什么。"
                    "不要编造不存在的告警、工单、巡检结果或现场结论。"
                ),
            },
            {
                "role": "system",
                "content": "以下是可供参考的电站上下文 JSON：\n" + json.dumps(operations_context, ensure_ascii=False),
            },
        ]

    messages.extend(normalize_history(history))
    messages.append({"role": "user", "content": user_message.strip()})
    return messages


def call_llm(messages):
    config = llm_config()
    payload = {
        "model": config["model"],
        "messages": list(messages),
        "temperature": 0.45,
        "max_tokens": 700,
        "stream": False,
    }
    req = request.Request(
        config["api_url"],
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=config["timeout"]) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"LLM network error: {exc.reason}") from exc

    parsed = json.loads(body)
    content = (((parsed.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("LLM returned empty content")
    return content
