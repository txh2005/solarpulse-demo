<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { fetchAiAdvice, fetchAnomalies, fetchMetrics, fetchPowerCurve, fetchSubArrays } from "../api/solar";
import AiAdvicePanel from "../components/AiAdvicePanel.vue";
import ChatAssistant from "../components/ChatAssistant.vue";
import MetricCards from "../components/MetricCards.vue";
import PowerChart from "../components/PowerChart.vue";
import SubArrayHealth from "../components/SubArrayHealth.vue";
import { getUserInfo, logout } from "../utils/auth";

const router = useRouter();
const metrics = ref({});
const curve = ref([]);
const anomalies = ref([]);
const advice = ref({});
const subArrays = ref([]);
const loading = ref(true);
const error = ref("");
const user = ref(getUserInfo());

const displayName = computed(() => user.value?.nickname || "系统管理员");
const roleName = computed(() => user.value?.roleName || "系统管理员");

async function loadDashboard() {
  loading.value = true;
  error.value = "";
  try {
    const [metricsData, curveData, anomalyData, adviceData, subArrayData] = await Promise.all([
      fetchMetrics(),
      fetchPowerCurve(),
      fetchAnomalies(),
      fetchAiAdvice(),
      fetchSubArrays(),
    ]);
    metrics.value = metricsData;
    curve.value = curveData;
    anomalies.value = anomalyData;
    advice.value = adviceData;
    subArrays.value = subArrayData;
  } catch {
    error.value = "无法连接 SolarPulse 数据服务，请确认 Django 服务运行在 127.0.0.1:8000。";
  } finally {
    loading.value = false;
  }
}

function handleLogout() {
  logout();
  router.replace("/login");
}

onMounted(loadDashboard);
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <span class="solar-mark"><i /></span>
        <div><strong>SolarPulse</strong><small>光伏智能运维平台</small></div>
      </div>

      <nav aria-label="主导航">
        <a class="active" href="#overview">运行总览</a>
        <a href="#forecast">功率预测</a>
        <a href="#diagnosis">异常诊断</a>
        <a href="#assistant">AI 助手</a>
      </nav>

      <div class="station-state user-state">
        <div>
          <strong>{{ displayName }}</strong>
          <span>{{ roleName }} · 演示环境</span>
        </div>
        <button type="button" class="logout-button" @click="handleLogout">退出登录</button>
      </div>
    </header>

    <main id="overview">
      <section class="page-heading">
        <div>
          <span>运行中心 / 2026.06.22</span>
          <h1>发电运行总览</h1>
          <p>预测偏差不是故障结论。系统结合辐照度与连续性规则决定是否报警。</p>
        </div>
        <div class="status-summary">
          <div><span>运行状态</span><strong class="warning-text">{{ metrics.active_alerts || 0 }} 项告警待研判</strong></div>
          <div><span>数据连接</span><strong class="normal-text">实时在线</strong></div>
          <button type="button" @click="loadDashboard" :disabled="loading">{{ loading ? "同步中..." : "刷新数据" }}</button>
        </div>
      </section>

      <div v-if="error" class="api-error" role="alert">
        <div><strong>接口连接失败</strong><p>{{ error }}</p></div>
        <button type="button" @click="loadDashboard">重试</button>
      </div>

      <template v-if="!error">
        <div v-if="loading" class="loading-state"><span /><p>正在同步电站、气象和功率数据...</p></div>
        <template v-else>
          <MetricCards :metrics="metrics" />

          <section class="decision-layout">
            <div id="forecast"><PowerChart :data="curve" :anomaly="advice" /></div>
            <div id="diagnosis"><AiAdvicePanel :advice="advice" :anomalies="anomalies" /></div>
          </section>

          <section class="bottom-layout">
            <SubArrayHealth :items="subArrays" />
            <div id="assistant"><ChatAssistant /></div>
          </section>
        </template>
      </template>

      <footer class="page-footer">
        <div><span><i />数据源：Django ORM</span><span>预测模型：PF-24H-RULE</span><span>时区：UTC+8</span></div>
        <p>SolarPulse 运维原型 · 已接入 MySQL</p>
      </footer>
    </main>
  </div>
</template>
