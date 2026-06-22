<script setup>
defineProps({
  advice: { type: Object, default: () => ({}) },
  anomalies: { type: Array, default: () => [] },
});
</script>

<template>
  <aside class="workspace advice-panel" data-testid="advice-panel">
    <header class="section-header">
      <div>
        <span>02 / AI 异常诊断</span>
        <h2>运维研判</h2>
      </div>
      <strong :class="['priority', `priority-${(advice.priority || 'low').toLowerCase()}`]">{{ advice.priority === 'HIGH' ? '高优先级' : advice.priority === 'MEDIUM' ? '中优先级' : '低优先级' }}</strong>
    </header>

    <section :class="['decision-conclusion', { warning: advice.has_anomaly }]">
      <div class="decision-label"><i />异常结论</div>
      <h3>{{ advice.has_anomaly ? '5号子阵列持续功率偏差' : '未发现严重异常' }}</h3>
      <p>{{ advice.has_anomaly ? `${advice.start_time}–${advice.end_time} 连续低于预测值，需安排优先排查。` : '当前功率偏差处于规则允许范围。' }}</p>
    </section>

    <section class="cause-section">
      <div class="decision-label"><i />原因判断</div>
      <strong>{{ advice.likely_cause === 'LOCAL_EQUIPMENT_OR_SHADING' ? '局部设备或遮挡问题' : '天气资源或预测误差' }}</strong>
      <p>{{ advice.summary || '正在从后端规则引擎读取诊断结果。' }}</p>
    </section>

    <section class="impact-section">
      <div class="decision-label"><i />影响评估</div>
      <dl class="diagnosis-stats">
        <div><dt>最大偏差</dt><dd>{{ advice.has_anomaly ? `${advice.max_deviation_percent}%` : '0%' }}</dd></div>
        <div><dt>预计损失</dt><dd class="loss-value">{{ advice.has_anomaly ? `${advice.estimated_loss_mwh} MWh` : '0 MWh' }}</dd></div>
        <div><dt>平均 GHI</dt><dd>{{ advice.has_anomaly ? `${advice.avg_ghi_wm2} W/m²` : '—' }}</dd></div>
      </dl>
    </section>

    <section class="action-list decision-actions">
      <h4><i />建议动作</h4>
      <ol>
        <li v-for="(action, index) in advice.actions || []" :key="action"><span>{{ String(index + 1).padStart(2, '0') }}</span>{{ action }}</li>
      </ol>
    </section>

    <section v-if="anomalies.length" class="event-record">
      <span>异常事件记录</span>
      <strong>{{ anomalies[0].anomaly_type === 'POWER_DEVIATION' ? '功率偏差事件' : anomalies[0].anomaly_type }}</strong>
      <p>状态 {{ anomalies[0].severity === 'MEDIUM' ? '中等' : anomalies[0].severity }} · 数据已写入 ORM</p>
    </section>
  </aside>
</template>
