export const DEMO_USER = {
  username: "admin",
  password: "123456",
  nickname: "系统管理员",
  roleName: "系统管理员",
  roleCode: "admin",
};

export function getToken() {
  return localStorage.getItem("token");
}

export function getUserInfo() {
  const raw = localStorage.getItem("userInfo");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function loginWithDemoUser() {
  localStorage.setItem("token", "demo-token");
  localStorage.setItem(
    "userInfo",
    JSON.stringify({
      username: DEMO_USER.username,
      nickname: DEMO_USER.nickname,
      roleName: DEMO_USER.roleName,
      roleCode: DEMO_USER.roleCode,
    }),
  );
  localStorage.setItem("roles", JSON.stringify([DEMO_USER.roleCode]));
  localStorage.setItem("permissions", JSON.stringify(["*"]));
}

export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("userInfo");
  localStorage.removeItem("roles");
  localStorage.removeItem("permissions");
}

export function validateDemoCredentials(username, password) {
  return username === DEMO_USER.username && password === DEMO_USER.password;
}
