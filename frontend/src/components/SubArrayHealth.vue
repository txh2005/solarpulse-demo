<script setup>
defineProps({
  items: { type: Array, default: () => [] },
});

function displayName(name) {
  return name.replace("Sub-array", "子阵列");
}

function displayOrientation(orientation) {
  return orientation === "South-East" ? "东南向" : orientation === "South-West" ? "西南向" : orientation;
}
</script>

<template>
  <section class="workspace health-workspace">
    <header class="section-header health-header">
      <div>
        <span>03 / 子阵列健康</span>
        <h2>子阵列健康状态</h2>
        <p>逆变器与子阵列运行概览</p>
      </div>
      <strong>{{ items.filter((item) => item.status === 'NORMAL').length }}/{{ items.length }} 正常</strong>
    </header>
    <div class="health-list">
      <article v-for="item in items" :key="item.id" :class="['health-row', { warning: item.status !== 'NORMAL' }]">
        <span class="health-dot" />
        <div><strong>{{ displayName(item.name) }}</strong><small>{{ item.inverter_id }} · {{ item.capacity_mw }} MW</small></div>
        <span class="health-orientation">{{ displayOrientation(item.orientation) }}</span>
        <b>{{ item.status === 'NORMAL' ? '正常' : '需关注' }}</b>
      </article>
    </div>
  </section>
</template>
