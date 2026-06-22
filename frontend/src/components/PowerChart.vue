<script setup>
import * as echarts from "echarts/core";
import { LineChart } from "echarts/charts";
import { GridComponent, LegendComponent, MarkAreaComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

echarts.use([LineChart, GridComponent, LegendComponent, MarkAreaComponent, TooltipComponent, CanvasRenderer]);

const props = defineProps({
  data: { type: Array, default: () => [] },
  anomaly: { type: Object, default: null },
});

const chartElement = ref(null);
let chart;
let observer;

const chartOption = computed(() => ({
  animationDuration: 700,
  animationEasing: "cubicOut",
  grid: { left: 52, right: 28, top: 42, bottom: 42 },
  tooltip: {
    trigger: "axis",
    backgroundColor: "#ffffff",
    borderColor: "rgba(37,99,235,.18)",
    textStyle: { color: "#0f172a", fontSize: 11 },
    padding: 12,
    formatter: (params) => {
      const point = props.data[params[0].dataIndex];
      const actual = point.actual_power_mw;
      const deviation = point.deviation_percent;
      return [
        `<b style="font-family:monospace">${point.time}</b>`,
        `预测功率　　　${Number(point.predicted_power_mw).toFixed(1)} MW`,
        `实际功率　　　${actual == null ? "暂无" : Number(actual).toFixed(1) + " MW"}`,
        `偏差率　　　　${deviation == null ? "暂无" : Number(deviation).toFixed(1) + "%"}`,
        `GHI 辐照度　　${point.ghi_wm2} W/m²`,
        `PR 性能比　　 ${Number(point.pr_value).toFixed(1)}%`,
      ].join("<br/>");
    },
  },
  legend: {
    right: 20,
    top: 4,
    itemWidth: 22,
    itemHeight: 2,
    textStyle: { color: "#64748b", fontSize: 10 },
    data: ["预测功率", "实际功率"],
  },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: props.data.map((point) => point.time),
    axisLine: { lineStyle: { color: "rgba(148,163,184,.35)" } },
    axisTick: { show: false },
    axisLabel: { color: "#64748b", fontFamily: "monospace", interval: 2, fontSize: 10 },
  },
  yAxis: {
    type: "value",
    name: "功率 MW",
    nameTextStyle: { color: "#64748b", fontSize: 9, align: "left" },
    min: 0,
    max: 52,
    interval: 10,
    axisLabel: { color: "#64748b", fontFamily: "monospace", fontSize: 10 },
    splitLine: { lineStyle: { color: "rgba(148,163,184,.25)", type: "dashed" } },
  },
  series: [
    {
      name: "预测功率",
      type: "line",
      smooth: 0.38,
      showSymbol: false,
      data: props.data.map((point) => point.predicted_power_mw),
      lineStyle: { color: "#38bdf8", width: 2, type: "dashed" },
      itemStyle: { color: "#38bdf8" },
    },
    {
      name: "实际功率",
      type: "line",
      smooth: 0.28,
      connectNulls: false,
      showSymbol: false,
      data: props.data.map((point) => point.actual_power_mw),
      lineStyle: { color: "#22c55e", width: 2.5 },
      itemStyle: { color: "#22c55e" },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "rgba(34,197,94,.18)" },
          { offset: 1, color: "rgba(34,197,94,0)" },
        ]),
      },
      markArea: props.anomaly?.has_anomaly
        ? {
            silent: true,
            itemStyle: { color: "rgba(249,115,22,.10)", borderColor: "rgba(249,115,22,.55)", borderWidth: 1 },
            data: [[{ xAxis: props.anomaly.start_time }, { xAxis: props.anomaly.end_time }]],
          }
        : undefined,
    },
  ],
}));

function renderChart() {
  if (!chartElement.value) return;
  if (!chart) chart = echarts.init(chartElement.value, null, { renderer: "canvas" });
  chart.setOption(chartOption.value, true);
}

onMounted(async () => {
  await nextTick();
  renderChart();
  observer = new ResizeObserver(() => chart?.resize());
  observer.observe(chartElement.value);
});

watch(chartOption, renderChart, { deep: true });

onBeforeUnmount(() => {
  observer?.disconnect();
  chart?.dispose();
});
</script>

<template>
  <section class="workspace chart-workspace">
    <header class="section-header">
      <div>
        <span>01 / 发电预测</span>
        <h2>预测功率 vs 实际功率</h2>
        <p>24 小时功率曲线 · 数据由 Django 数据服务提供</p>
      </div>
      <div class="freshness"><i />实时数据</div>
    </header>
    <div v-if="data.length" ref="chartElement" class="power-chart" data-testid="power-chart" />
    <div v-else class="empty-state">暂无功率曲线数据，请先运行 seed_demo_data。</div>
    <footer class="rule-strip">
      <span>规则引擎</span>
      <p>夜间不判断 · 低 GHI 优先天气 · 单点不报警 · 连续 2 点偏差 &gt; 20% 触发</p>
      <b :class="anomaly?.has_anomaly ? 'danger' : ''"><i />{{ anomaly?.has_anomaly ? '已检测异常' : '运行正常' }}</b>
    </footer>
  </section>
</template>
