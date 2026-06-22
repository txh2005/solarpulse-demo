<script setup>
import { computed, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { DEMO_USER, loginWithDemoUser, validateDemoCredentials } from "../../utils/auth";

const router = useRouter();
const route = useRoute();
const loading = ref(false);
const error = ref("");

const form = reactive({
  username: "",
  password: "",
  remember: true,
});

const redirectPath = computed(() => {
  const redirect = route.query.redirect;
  return typeof redirect === "string" && redirect ? redirect : "/dashboard";
});

function finishLogin() {
  loginWithDemoUser();
  router.replace(redirectPath.value);
}

async function submitLogin() {
  error.value = "";
  loading.value = true;

  await new Promise((resolve) => setTimeout(resolve, 450));

  if (validateDemoCredentials(form.username, form.password)) {
    finishLogin();
    return;
  }

  loading.value = false;
  error.value = "账号或密码错误，请使用演示账号：admin / 123456";
}

function quickEnter() {
  form.username = DEMO_USER.username;
  form.password = DEMO_USER.password;
  error.value = "";
  finishLogin();
}
</script>

<template>
  <div class="login-page">
    <div class="login-orb login-orb-left" />
    <div class="login-orb login-orb-right" />

    <section class="login-layout">
      <div class="login-intro">
        <div class="login-brand">
          <span class="solar-mark"><i /></span>
          <div>
            <strong>SolarPulse</strong>
            <small>光伏智能运维平台</small>
          </div>
        </div>

        <span class="login-kicker">面试演示环境</span>
        <h1>光伏智能运维与发电预测系统</h1>
        <p>面向光伏电站的设备监控、告警管理、运维工单与发电预测平台</p>

        <div class="login-highlights">
          <div>
            <span>演示账号</span>
            <strong>{{ DEMO_USER.username }}</strong>
          </div>
          <div>
            <span>演示密码</span>
            <strong>{{ DEMO_USER.password }}</strong>
          </div>
          <div>
            <span>当前角色</span>
            <strong>{{ DEMO_USER.roleName }}</strong>
          </div>
        </div>

        <p class="login-note">当前为面试演示环境，使用模拟数据展示核心功能。</p>
      </div>

      <div class="login-panel">
        <div class="login-panel-header">
          <span>账号登录</span>
          <h2>进入演示系统</h2>
          <p>使用固定账号登录后，即可查看系统首页与核心功能。</p>
        </div>

        <form class="login-form" @submit.prevent="submitLogin">
          <label class="login-field">
            <span>用户名</span>
            <input v-model.trim="form.username" type="text" placeholder="请输入用户名" autocomplete="username" />
          </label>

          <label class="login-field">
            <span>密码</span>
            <input v-model="form.password" type="password" placeholder="请输入密码" autocomplete="current-password" />
          </label>

          <label class="login-check">
            <input v-model="form.remember" type="checkbox" />
            <span>记住我</span>
          </label>

          <p v-if="error" class="login-error">{{ error }}</p>

          <button class="login-submit" type="submit" :disabled="loading">
            {{ loading ? "登录中..." : "登录" }}
          </button>

          <button class="login-demo" type="button" @click="quickEnter">
            一键进入演示系统
          </button>
        </form>
      </div>
    </section>
  </div>
</template>
