import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "../views/Dashboard.vue";
import Login from "../views/login/Login.vue";
import { getToken } from "../utils/auth";

const routes = [
  {
    path: "/",
    redirect: "/dashboard",
  },
  {
    path: "/login",
    name: "login",
    component: Login,
    meta: { public: true },
  },
  {
    path: "/dashboard",
    name: "dashboard",
    component: Dashboard,
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/dashboard",
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const token = getToken();

  if (to.path === "/login") {
    if (token) {
      next("/dashboard");
    } else {
      next();
    }
    return;
  }

  if (!token) {
    next({
      path: "/login",
      query: {
        redirect: to.fullPath,
      },
    });
    return;
  }

  next();
});

export default router;
