<script setup>
import { nextTick, ref } from "vue";
import { sendAssistantMessage } from "../api/solar";

const messages = ref([
  {
    role: "assistant",
    content: "你好，我是 SolarPulse AI 助手。日常聊天、普通问题和电站运维分析我都可以处理。",
  },
]);

const input = ref("");
const loading = ref(false);
const chatLog = ref(null);
const quickQuestions = ["分析今日发电异常", "PR 值是什么？", "是否需要清洗？", "检查逆变器"];

function buildHistory() {
  return messages.value.slice(-6).map((item) => ({ role: item.role, content: item.content }));
}

async function send(content = input.value) {
  const message = content.trim();
  if (!message || loading.value) return;

  const history = buildHistory();
  messages.value.push({ role: "user", content: message });
  input.value = "";
  loading.value = true;

  try {
    const response = await sendAssistantMessage(message, history);
    messages.value.push({ role: "assistant", content: response.reply });
  } catch (error) {
    messages.value.push({ role: "assistant", content: "助手服务暂时不可用，请检查 Django 数据服务、模型接口或网络连接。" });
  } finally {
    loading.value = false;
    await nextTick();
    if (chatLog.value) chatLog.value.scrollTop = chatLog.value.scrollHeight;
  }
}
</script>

<template>
  <section class="workspace assistant-workspace">
    <header class="section-header assistant-title">
      <div>
        <span>04 / 智能运维助手</span>
        <h2>AI 运维助手</h2>
      </div>
      <div class="freshness"><i />接口在线</div>
    </header>
    <div class="assistant-body">
      <nav class="quick-list" aria-label="快捷问题">
        <span>快捷问题</span>
        <button v-for="question in quickQuestions" :key="question" type="button" @click="send(question)">{{ question }}</button>
      </nav>
      <div class="conversation">
        <div ref="chatLog" class="chat-log" aria-live="polite" data-testid="chat-log">
          <div v-for="(message, index) in messages" :key="index" :class="['chat-message', message.role]">
            <span>{{ message.role === "assistant" ? "助手" : "我" }}</span>
            <p>{{ message.content }}</p>
          </div>
          <div v-if="loading" class="chat-message assistant"><span>助手</span><p>正在生成回复，请稍候...</p></div>
        </div>
        <form class="chat-form" @submit.prevent="send()">
          <input v-model="input" aria-label="向 SolarPulse AI 提问" placeholder="输入任何问题，或直接询问电站异常" data-testid="chat-input" />
          <button type="submit" :disabled="!input.trim() || loading" data-testid="chat-send">发送 →</button>
        </form>
      </div>
    </div>
  </section>
</template>
