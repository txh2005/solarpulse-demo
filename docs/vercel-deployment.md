# Vercel 部署方案

本文档对应当前项目建议的线上演示架构：

`Vercel 承载前端 + Vercel 代理 /api + Django 后端单独部署 + MySQL 远程库`

## 一、最终架构

```text
面试官浏览器
    ↓
Vercel 前端站点
    ├─ /                Vue 页面
    └─ /api/*           Vercel 代理函数
                          ↓
                    Django API 服务
                          ↓
                      远程 MySQL
```

这样做的好处是：

- 面试官只访问一个域名
- 浏览器里不会暴露 Django 实际地址
- 前端调用统一走 `/api`
- 后端可独立扩容和替换

## 二、前端已完成的适配

当前项目已经做了以下处理：

- 生产环境默认请求 `/api`
- 本地开发默认请求 `http://127.0.0.1:8000/api`
- 已新增 `frontend/api/[...path].js` 作为 Vercel 代理函数
- 已保留 `frontend/vercel.json` 处理 Vue 单页路由刷新

## 三、你需要准备的两个线上服务

### 1）Vercel 前端项目

建议把 `frontend` 目录作为 Vercel 的 Root Directory。

构建配置：

- Framework Preset：Vite
- Build Command：`pnpm build`
- Output Directory：`dist`
- Install Command：`pnpm install`

### 2）Django 后端服务

后端不要部署在 Vercel，建议部署到支持 Python 常驻服务的平台，例如：

- Railway
- Render
- 云服务器
- 其他支持 Django + MySQL 的 PaaS

后端需要能够通过公网 HTTPS 域名访问，例如：

`https://solarpulse-api.example.com`

## 四、Vercel 环境变量

在 Vercel 项目中配置：

```env
BACKEND_API_ORIGIN=https://你的-Django-后端域名
PROXY_TIMEOUT_MS=60000
```

示例：

```env
BACKEND_API_ORIGIN=https://solarpulse-api.example.com
PROXY_TIMEOUT_MS=60000
```

说明：

- 不要在末尾加 `/api`
- 代理函数会自动拼接为 `https://你的域名/api/...`

## 五、Django 后端环境变量

建议基于 [backend/.env.example](../backend/.env.example) 配置。

线上至少要设置：

```env
DEBUG=false
SECRET_KEY=请替换为随机密钥

ALLOWED_HOSTS=你的后端域名
CORS_ALLOWED_ORIGINS=https://你的-vercel-域名.vercel.app

DB_ENGINE=mysql
DB_NAME=solarpulse
DB_USER=你的数据库用户名
DB_PASSWORD=你的数据库密码
DB_HOST=你的 MySQL 主机
DB_PORT=3306

LLM_API_KEY=你的模型密钥
LLM_API_URL=https://api.deepseek.com/chat/completions
LLM_MODEL=deepseek-chat
LLM_TIMEOUT_SECONDS=45
```

如果你绑定了正式自定义域名，也要一并加入：

- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`

## 六、远程 MySQL 初始化

先在远程 MySQL 创建数据库：

```sql
CREATE DATABASE solarpulse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

然后在后端部署环境执行：

```bash
python manage.py migrate
python manage.py seed_demo_data
```

这样面试官打开页面后就能直接看到完整演示数据。

## 七、推荐部署顺序

### 第一步：先部署 Django 后端

确保这些地址可正常访问：

- `/api/metrics/`
- `/api/power-curve/`
- `/api/assistant/`

例如：

`https://你的后端域名/api/metrics/`

返回 JSON 即表示后端正常。

### 第二步：再部署 Vercel 前端

把仓库导入 Vercel 后：

- Root Directory 选 `frontend`
- 填写 `BACKEND_API_ORIGIN`
- 点击 Deploy

部署完成后，前端会通过 Vercel 代理自动访问后端。

## 八、面试演示前检查清单

- 登录页可访问：`/login`
- 演示账号 `admin / 123456` 可正常登录
- `/dashboard` 可加载指标卡片和图表
- AI 运维助手可普通聊天
- 询问电站问题时能进入专业回答
- 刷新页面不会出现 404
- `/api/assistant/` 响应正常

## 九、常见问题

### 1）前端页面打开了，但数据全空

优先检查：

- Vercel 是否设置了 `BACKEND_API_ORIGIN`
- Django 后端是否真的已公网可访问
- 后端是否已执行 `migrate` 和 `seed_demo_data`

### 2）AI 助手提示服务不可用

优先检查：

- Django 服务是否在线
- `LLM_API_KEY` 是否有效
- 模型接口供应商是否可访问
- 后端出站网络是否允许访问模型服务

### 3）刷新子页面 404

确认 `frontend/vercel.json` 已保留单页应用回退配置。

## 十、面试场景建议

如果你是给面试官演示，最稳的做法是：

1. 后端提前部署好并写入演示数据
2. 前端通过 Vercel 发布正式链接
3. 演示时只展示一个入口 URL
4. 登录后直接进入 `/dashboard`
5. 现场演示：
   - 指标卡片
   - 预测 vs 实际曲线
   - AI 异常诊断
   - AI 助手普通聊天与专业问答

这套方式对“产品完整度”和“工程可落地性”的观感都会更好。
