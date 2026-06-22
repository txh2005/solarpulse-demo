from decimal import Decimal

from django.utils import timezone


LOW_GHI_THRESHOLD = 300
HIGH_GHI_THRESHOLD = 650
DEVIATION_THRESHOLD = Decimal("0.20")


def build_curve_rows(forecasts, actuals, weather_records):
    actual_by_time = {item.record_time: item for item in actuals}
    weather_by_time = {item.record_time: item for item in weather_records}
    rows = []

    for forecast in forecasts:
        actual = actual_by_time.get(forecast.forecast_time)
        weather = weather_by_time.get(forecast.forecast_time)
        predicted = float(forecast.predicted_power_mw)
        actual_power = float(actual.actual_power_mw) if actual else None
        deviation = None

        if predicted > 0 and actual_power is not None:
            deviation = round(((predicted - actual_power) / predicted) * 100, 2)

        rows.append(
            {
                "time": timezone.localtime(forecast.forecast_time).strftime("%H:%M"),
                "predicted_power_mw": predicted,
                "actual_power_mw": actual_power,
                "ghi_wm2": weather.ghi_wm2 if weather else 0,
                "pr_value": float(actual.pr_value) if actual else 0,
                "weather_status": weather.weather_status if weather else "未知",
                "deviation_percent": deviation,
            }
        )

    return rows


def detect_anomaly(curve_data):
    abnormal_groups = []
    current_group = []

    for point in curve_data:
        predicted = point.get("predicted_power_mw") or 0
        actual = point.get("actual_power_mw")
        ghi = point.get("ghi_wm2") or 0

        # 夜间或预测为 0 时不判断异常。
        if predicted <= 0 or actual is None:
            if len(current_group) >= 2:
                abnormal_groups.append(current_group)
            current_group = []
            continue

        # 低辐照度下优先视为天气影响，不直接触发设备异常。
        if ghi < LOW_GHI_THRESHOLD:
            if len(current_group) >= 2:
                abnormal_groups.append(current_group)
            current_group = []
            continue

        deviation = Decimal(str((predicted - actual) / predicted))
        if deviation > DEVIATION_THRESHOLD:
            current_group.append({**point, "deviation_ratio": float(deviation)})
        else:
            if len(current_group) >= 2:
                abnormal_groups.append(current_group)
            current_group = []

    if len(current_group) >= 2:
        abnormal_groups.append(current_group)

    if not abnormal_groups:
        return {"has_anomaly": False}

    group = abnormal_groups[0]
    max_deviation = max(item["deviation_ratio"] for item in group) * 100
    avg_ghi = sum(item["ghi_wm2"] for item in group) / len(group)
    estimated_loss = sum(max(0, item["predicted_power_mw"] - item["actual_power_mw"]) for item in group)
    likely = "CLOUD_SHADING" if avg_ghi < HIGH_GHI_THRESHOLD else "LOCAL_EQUIPMENT_OR_SHADING"

    return {
        "has_anomaly": True,
        "start_time": group[0]["time"],
        "end_time": group[-1]["time"],
        "max_deviation_percent": round(max_deviation, 2),
        "estimated_loss_mwh": round(estimated_loss, 2),
        "avg_ghi_wm2": round(avg_ghi),
        "likely_cause": likely,
        "priority": "HIGH" if max_deviation >= 35 else "MEDIUM",
    }


def build_advice_from_detection(detection):
    if not detection.get("has_anomaly"):
        return {
            "title": "未发现关键异常",
            "summary": "当前未发现连续两个有效采样点超过 20% 的功率偏差。",
            "actions": ["保持常规监控", "继续跟踪 PR 值和 GHI 趋势"],
            "priority": "LOW",
        }

    cause_text = (
        "同期 GHI 偏低，优先判断为短时云层遮挡或预测偏差。"
        if detection["likely_cause"] == "CLOUD_SHADING"
        else "同期 GHI 仍处于较高水平，优先排查子阵列遮挡、逆变器降额、组串失配、组件积灰或传感器异常。"
    )

    return {
        "title": "检测到发电偏差",
        "summary": (
            f"{detection['start_time']}–{detection['end_time']} 检测到实际功率连续低于预测功率，"
            f"最大偏差约 {detection['max_deviation_percent']}%。{cause_text}"
        ),
        "actions": [
            "对比相邻子阵列输出，确认属于全站下降还是局部下降。",
            "检查 INV-005 逆变器、MPPT 状态与告警代码。",
            "查看组串电流离散度、IV 曲线与最近清洗记录。",
            "必要时安排热成像或现场巡检复核。",
        ],
        "priority": detection["priority"],
    }


def assistant_reply(message, detection):
    text = (message or "").strip().lower()
    advice = build_advice_from_detection(detection)

    if any(keyword in text for keyword in ["你好", "您好", "hi", "hello"]):
        return "你好，我是 SolarPulse AI 助手。日常问题我可以直接聊；如果你想分析发电异常、PR、清洗或逆变器，我也可以结合当前电站数据给出专业建议。"

    if any(keyword in text for keyword in ["你是谁", "你能做什么", "help", "帮助"]):
        return "我是一个可日常对话的 AI 助手，也能切换到光伏运维分析模式。你可以和我普通聊天，也可以直接问：分析今日发电异常、PR 值是什么、是否需要清洗、检查逆变器。"

    if "异常" in text or "分析" in text:
        if detection.get("has_anomaly"):
            action_text = "；".join(advice["actions"][:3])
            return f"{advice['summary']} 建议动作：{action_text}。预计损失约 {detection['estimated_loss_mwh']} MWh。"
        return "当前没有连续有效异常窗口。夜间、低辐照度和单点噪声都已被规则过滤，建议继续观察 PR 值和 GHI 趋势。"

    if "pr" in text:
        return "PR 值即 Performance Ratio，用于衡量电站在当前太阳资源条件下的发电效率。若 PR 持续下滑，应重点排查积灰、遮挡、逆变器效率、组串失配和限发情况。"

    if "清洗" in text:
        return "清洗建议应结合近 7 到 10 天的 PR 趋势、近期降雨和历史清洗记录综合判断。若 GHI 正常但 PR 持续下降，可以测算清洗收益并安排在低发电时段执行。"

    if "逆变器" in text:
        return "建议检查逆变器告警代码、MPPT 状态、直流输入电压电流、交流输出以及是否存在限功率运行。若异常集中在某个子阵列，可优先查看对应逆变器。"

    return "当然可以，我们也可以像普通 AI 助手一样聊天。若你需要切换到电站专业分析，只要直接提问发电异常、PR、清洗或逆变器问题即可。"
