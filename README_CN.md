<p align="center">
  <h1 align="center">🐾 OpenClawCM</h1>
  <p align="center"><strong>多实例 AI Agent 统一管控平台</strong></p>
  <p align="center">
    <a href="README.md">English</a> · <a href="docs/TECHNICAL.md">技术文档</a> · <a href="docs/TECHNICAL_EN.md">Technical Docs</a>
  </p>
</p>

---

## 痛点与愿景

当你的组织同时运行数十个 OpenClaw 实例、上百个 AI Agent 时，你会面对：

- **孤岛式管理** — 每个实例各自为政，缺乏全局视角
- **协作黑箱** — 多 Agent 协作流程靠 JSON 手写路由规则，出错难排查
- **输出散落** — 代码、文档、日志分散在各节点，无法统一检索与复用
- **记忆碎片** — Agent 历史上下文各自独立，跨 Agent 知识无法共享

**OpenClawCM** 正是为解决这些问题而生。它提供一个 **集中式 Web 管理面板**，让你用一套界面完成实例接入、Agent 编排、协作流程可视化设计、统一输出管理与全文检索，同时内置共享记忆池机制实现跨 Agent 知识复用。

---

## 核心能力

| 能力 | 描述 |
|------|------|
| **实例管理** | 多 OpenClaw 实例集中注册、分组、健康探测 |
| **Agent 全生命周期** | 创建 → 配置模型/Prompt → 绑定技能 → 启停控制 |
| **可视化流程编排** | 基于 Vue Flow 的拖拽式 DAG 编辑器，支持 5 种节点类型 |
| **共享记忆池** | 跨 Agent 共享上下文，支持读/写/只读权限控制 |
| **统一输出中心** | 7 种输出类型 + FTS5 全文检索 + 语法高亮 + Markdown 渲染 |
| **模型供应商管理** | 多 LLM 供应商接入，全局/实例/Agent 三级模型配置 |
| **审计与安全** | JWT 认证、RBAC 三级角色、全操作审计日志 |

---

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                    Nginx (端口 80)                        │
│         SPA 静态资源  │  /api/ 反向代理                   │
└──────────┬───────────┴───────────────┬───────────────────┘
           │                           │
┌──────────▼──────────┐   ┌────────────▼──────────────────┐
│   Vue 3 Frontend    │   │      FastAPI Backend          │
│  Element Plus + UI  │   │  SQLAlchemy Async ORM         │
│  Vue Flow 流程编辑   │   │  JWT Auth + RBAC              │
│  Pinia 状态管理      │   │  审计中间件                    │
└─────────────────────┘   └────────────┬──────────────────┘
                                       │
                          ┌────────────▼──────────────────┐
                          │   SQLite (FTS5) / MySQL       │
                          │   17 张数据表 + 全文索引        │
                          └───────────────────────────────┘
```

---

## 快速开始

### Docker Compose（推荐）

```bash
git clone https://github.com/your-org/openclawcm.git
cd openclawcm

# 按需修改环境变量
# vim docker-compose.yml

docker compose up -d
```

启动后访问 **http://localhost** ，默认账号 `admin / admin123`。

### 本地开发

```bash
# 后端
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（新终端）
cd frontend
npm install
npm run dev
```

前端默认 http://localhost:5173 ，后端 API http://localhost:8000 。

---

## 项目结构

```
openclawcm/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口 + 启动事件
│   │   ├── config.py            # 环境配置 (.env)
│   │   ├── database.py          # 异步数据库引擎 + FTS5
│   │   ├── models/              # 15 个 ORM 模型
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── api/v1/              # 10 个路由模块 (86 端点)
│   │   ├── middleware/          # 审计日志中间件
│   │   └── utils/               # 响应封装 + 认证工具
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/index.js         # Axios API 封装 (76 方法)
│   │   ├── router/index.js      # 11 个路由
│   │   ├── views/               # 10 个页面视图
│   │   ├── layouts/             # 主布局 (侧栏+顶栏)
│   │   └── stores/              # Pinia 状态
│   ├── package.json
│   └── Dockerfile
├── tests/
│   └── integration_test.sh      # 79 个集成测试
├── docker-compose.yml
└── nginx.conf
```

---

## 功能模块

### 📊 仪表盘

实例/Agent/输出总量统计卡片、最近输出时间线、异常告警列表。

### 🖥️ 实例管理

注册多个 OpenClaw 实例，分组管理，记录 API Key，自动心跳检测。

### 🤖 Agent 管理

完整的 Agent 生命周期管理，包括：
- 基础信息与系统 Prompt 配置
- 模型绑定（LLM 供应商 → 模型配置 → Agent）
- Memory 配置（类型/历史消息数/Token 上限/持久化/自动清理）
- 技能绑定/解绑
- 一键启动/停止

### 🔗 协作流程编辑器

拖拽式 DAG 可视化编辑器，支持：
- **5 种节点**：开始、结束、Agent、条件分支、并行网关
- 连线与条件路由配置
- 实时属性编辑面板
- 布局自动保存（节点坐标 + 视口状态）
- 保存为模板复用

### 📝 输出管理

统一收集所有 Agent 的 7 种输出类型（CODE / DOCUMENT / LOG / REPORT / DATA / IMAGE / OTHER）：
- FTS5 全文检索
- 代码语法高亮（highlight.js，github-dark 主题）
- Markdown 实时渲染
- 收藏、标签、单条/批量导出、批量删除

### 🧠 共享记忆池

创建跨 Agent 的共享记忆空间，支持：
- 多种记忆类型（buffer / summary / token_buffer）
- Agent 绑定与权限控制（read / write / readwrite）
- 关联协作流程

### 🔧 模型管理

两层结构：供应商（OpenAI / Anthropic / 自定义）→ 模型配置（temperature / max_tokens / top_p），支持全局/实例/Agent 三级作用域。

### 🔐 系统管理

- JWT 身份认证（24h 有效期）
- RBAC 角色（admin / operator / viewer）
- 全操作审计日志（自动记录 POST/PUT/DELETE）
- 用户管理（仅管理员）

---

## 技术亮点

- **全异步架构**：FastAPI + SQLAlchemy 2.0 async + aiosqlite，高并发低延迟
- **SQLite FTS5 全文搜索**：触发器自动同步索引，零额外依赖实现中文搜索
- **DAG 可视化编排**：Vue Flow 拖拽编辑 + 后端节点/边持久化 + 布局状态保存
- **统一响应规范**：`{code, message, data}` 标准格式，前后端一致
- **审计中间件**：零侵入自动记录所有写操作，从 JWT 提取操作人
- **数据库可迁移**：SQLite 开发 → MySQL 生产，无需改代码

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/openclawcm.db` | 数据库连接串 |
| `SECRET_KEY` | `openclawcm-secret-key-change-in-production` | JWT 签名密钥 |
| `CORS_ORIGINS` | `http://localhost:5173,...` | 允许的跨域来源 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token 有效期（分钟） |

---

## 测试

```bash
# 启动后端后运行集成测试
bash tests/integration_test.sh
```

当前测试覆盖 **79 个用例**，涵盖全部 API 端点的正向与异常路径。

---

## 许可证

[Apache License 2.0](LICENSE)
