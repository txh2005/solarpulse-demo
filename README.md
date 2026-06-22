# SolarPulse Dashboard

SolarPulse 是一个用于面试演示的光伏智能运维与发电预测系统原型，采用 Vue 3 + Vite 构建前端，Django REST Framework 构建后端，并通过规则引擎与大模型接口提供异常诊断和 AI 运维助手能力。

当前版本重点展示：

- 发电运行总览与核心 KPI
- 预测功率 vs 实际功率曲线
- 基于边界规则的异常识别
- AI 运维建议面板
- 支持日常对话与专业问答的 AI 助手
- 演示账号登录与基础路由守卫

## 项目结构

```text
SolarPulseFull/
├─ backend/                  Django + DRF + ORM
│  ├─ monitoring/            模型、API、规则、测试、seed
│  ├─ solarpulse/            Django 项目配置
│  └─ requirements.txt
├─ frontend/                 Vue 3 + Vite + ECharts + Axios
│  ├─ api/                   Vercel 代理函数
│  ├─ src/
│  └─ vercel.json
└─ docs/                     产品答卷、技术设计、部署说明
```

## 本地运行

### 1. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver 127.0.0.1:8000
```

### 2. 启动前端

```bash
cd frontend
pnpm install
copy .env.example .env
pnpm dev
```

浏览器访问：

[http://127.0.0.1:5173](http://127.0.0.1:5173)

## 演示账号

- 用户名：admin
- 密码：123456
- 角色：系统管理员

## 核心 API

| Method | Path | 说明 |
|---|---|---|
| GET | `/api/metrics/` | 实时运行指标 |
| GET | `/api/power-curve/` | 发电预测与实际曲线 |
| GET | `/api/anomalies/` | 异常事件列表 |
| GET | `/api/ai-advice/` | AI 运维诊断摘要 |
| GET | `/api/sub-arrays/` | 子阵列健康状态 |
| POST | `/api/assistant/` | AI 运维助手 |

## 业务规则亮点

- 夜间预测为 0 时不报警
- 低 GHI 导致的低发电优先判断为天气因素
- 单点异常不直接报警，需连续异常点触发
- 区分全站下降与局部下降
- 预测偏差不等于设备故障

## 部署方案

推荐采用：

- 前端：Vercel
- API 代理：Vercel Serverless Function
- 后端：独立部署 Django 服务
- 数据库：远程 MySQL

详细步骤见：

[docs/vercel-deployment.md](./docs/vercel-deployment.md)

## 验证命令

```bash
# Backend
cd backend
python manage.py test

# Frontend
cd frontend
pnpm build
```
