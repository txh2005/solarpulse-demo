<script setup>
defineProps({
  metrics: { type: Object, required: true },
});

const items = [
  { key: "current_power_mw", label: "当前总功率", unit: "MW", digits: 1 },
  { key: "today_generation_mwh", label: "今日累计发电量", unit: "MWh", digits: 1 },
  { key: "pr_value", label: "PR 性能比", unit: "%", digits: 1 },
  { key: "weather_status", label: "当前天气", unit: "", text: true },
  { key: "ghi_wm2", label: "GHI 辐照度", unit: "W/m²", digits: 0 },
  { key: "active_alerts", label: "当前异常数", unit: "", digits: 0, alert: true },
];

const weatherMap = {
  Sunny: "晴",
  Cloudy: "多云",
  Rainy: "雨",
  Unknown: "未知",
};

function displayValue(item, value) {
  if (item.text) return weatherMap[value] || value || "未知";
  return Number(value || 0).toLocaleString("zh-CN", {
    minimumFractionDigits: item.digits,
    maximumFractionDigits: item.digits,
  });
}
</script>

<template>
  <section class="metric-band" aria-label="实时运行指标">
    <article v-for="item in items" :key="item.key" :class="['metric-item', `metric-${item.key}`, { alert: item.alert && metrics[item.key] > 0 }]">
      <i class="metric-accent" />
      <span>{{ item.label }}</span>
      <strong>{{ displayValue(item, metrics[item.key]) }}<small>{{ item.unit }}</small></strong>
      <p v-if="item.key === 'current_power_mw'">装机容量 {{ metrics.capacity_mw }} MW</p>
      <p v-else-if="item.key === 'pr_value'">性能目标 82.0%</p>
      <p v-else-if="item.key === 'weather_status'">环境温度 {{ metrics.temperature_c }}℃</p>
      <p v-else-if="item.key === 'active_alerts'">需人工研判</p>
      <p v-else>数据源 · Django 数据服务</p>
    </article>
  </section>
</template>
