# OpenClawCM 技术文档

> 本文档简要介绍 OpenClawCM 的关键技术实现，供开发者快速了解系统内部工作原理。

---

## 1. 整体技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 前端框架 | Vue 3 (Composition API) | 3.5 |
| UI 组件库 | Element Plus | 2.13 |
| 流程编辑器 | @vue-flow/core + background/controls/minimap | 1.48 |
| 代码高亮 | highlight.js | 11.11 |
| Markdown 渲染 | marked | 17.0 |
| 数据可视化 | ECharts + vue-echarts | 5.6 / 7.0 |
| 构建工具 | Vite | 6.4 |
| 后端框架 | FastAPI | 0.128 |
| ORM | SQLAlchemy 2.0 (async) | 2.0.47 |
| 数据库 | SQLite (aiosqlite) / MySQL (aiomysql) | — |
| 认证 | python-jose (JWT HS256) + bcrypt | — |
| 部署 | Docker Compose (Nginx + uvicorn) | — |

---

## 2. 数据库设计

### 2.1 异步引擎初始化

```python
# database.py
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)
```

- SQLite 启用 **WAL 模式**（`PRAGMA journal_mode=WAL`），提升并发读写性能
- 生产环境可无缝切换 MySQL，只需修改 `DATABASE_URL`

### 2.2 数据模型概览（15 个模型，17 张表）

```
User ─┐
      ├─ AuditLog
      │
Instance ──┬── Agent ──┬── AgentSkill ←── Skill
           │           ├── AgentMemoryPoolBinding ←── SharedMemoryPool
           │           └── (model_config_id FK)
           │
ModelProvider ── ModelConfig
           │
Output ──┬── OutputTag
         └── OutputAttachment
           │
Collaboration ──┬── CollaborationNode (→ Agent)
                └── CollaborationEdge (→ Node × 2)

SystemSetting (K-V 配置表)
```

所有模型继承 `TimestampMixin`，自动维护 `created_at` / `updated_at`。

### 2.3 FTS5 全文搜索

```python
# 启动时自动创建 FTS 虚拟表
CREATE VIRTUAL TABLE IF NOT EXISTS outputs_fts
USING fts5(title, summary, content, content=outputs, content_rowid=id);

# 触发器保持 FTS 索引与 outputs 表同步
CREATE TRIGGER outputs_ai AFTER INSERT ON outputs BEGIN
    INSERT INTO outputs_fts(rowid, title, summary, content)
    VALUES (new.id, new.title, new.summary, new.content);
END;
```

查询时使用 `MATCH` + `rank` 排序，先获取 FTS rowid 列表，再用 `IN` 子句加载完整 ORM 对象（含关联关系），避免 N+1 问题。

---

## 3. 认证与授权

### 3.1 JWT 流程

```
客户端 POST /api/v1/auth/login {username, password}
    → bcrypt.checkpw(password, stored_hash)
    → jose.jwt.encode({sub: user_id, username, role}, SECRET_KEY, HS256)
    → 返回 {token, user} （有效期 24h）

后续请求 Header: Authorization: Bearer <token>
    → require_auth 依赖解码验证
    → require_admin 额外检查 role == "admin"
```

### 3.2 密码安全

使用 `bcrypt` 直接哈希，复杂度因子 12（默认），无 passlib 中间层。

### 3.3 角色权限

| 角色 | 权限 |
|------|------|
| `admin` | 完整读写 + 用户管理 + 审计日志查看 |
| `operator` | 实例/Agent/流程等业务操作 |
| `viewer` | 只读访问 |

### 3.4 路由级鉴权

所有 API 路由（除 auth 路由外）通过 router 级 `dependencies` 统一注入 `require_auth`：

```python
# router.py
api_router.include_router(instances.router, prefix="/instances",
                          dependencies=[Depends(require_auth)])
# auth 路由不添加 — login 是公开接口
api_router.include_router(auth.router, prefix="/auth")
```

未携带有效 Token 的请求将直接返回 `{"detail": "Not authenticated"}`。

---

## 4. API 设计

### 4.1 统一响应格式

```python
def success(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}

def error(message, code=400):
    return JSONResponse({"code": code, "message": message, "data": None}, status_code=200)

def page_response(data, total, page, page_size):
    return {"code": 200, "message": "success",
            "data": data, "total": total, "page": page, "page_size": page_size}
```

所有 API 统一返回 HTTP 200，业务错误通过 `code` 字段区分（400/401/404）。前端拦截器根据 `code` 统一处理。

### 4.2 防止 ORM 懒加载

异步 ORM 不支持隐式懒加载，所有需要关联数据的查询使用 `selectinload`：

```python
query = select(Output).options(
    selectinload(Output.instance),
    selectinload(Output.agent),
    selectinload(Output.tags),
)
```

手动构建响应字典（`_output_to_dict`），通过 `__dict__` 检查避免触发未加载的关联访问。

### 4.3 路由模块划分（10 个模块，89 端点）

| 模块 | 前缀 | 端点数 | 关键特性 |
|------|------|--------|----------|
| auth | `/auth` | 7 | JWT 登录、用户 CRUD |
| instances | `/instances` | 6 | 实例 CRUD + 健康检查 |
| models | `/models` | 9 | 供应商 + 模型配置 CRUD |
| agents | `/agents` | 12 | Agent CRUD + 启停 + 技能绑定 + agent_count同步 |
| skills | `/skills` | 7 | 技能 CRUD + 安装/卸载 |
| outputs | `/outputs` | 10 | 输出 CRUD + FTS + 标签 + 批量操作 |
| collaborations | `/collaborations` | 19 | 流程 + 节点 + 边 + 布局 + 控制 + 模板复制 |
| memory-pools | `/memory-pools` | 8 | 记忆池 CRUD + Agent 绑定 |
| dashboard | `/dashboard` | 7 | 统计概览 + 趋势 + Agent状态 + 输出类型 + 实例健康 |
| system | `/system` | 4 | 系统信息 + 审计日志 |

---

## 5. 审计中间件

```python
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.method in ("POST", "PUT", "DELETE"):
            # 从 Authorization header 解码 JWT 提取用户信息
            # 异步写入 audit_logs 表（asyncio.create_task + 0.5s 延迟避免 SQLite 锁）
        return response
```

- **零侵入**：无需在业务代码中手动记录日志
- **SQLite 锁规避**：审计写入延迟 0.5 秒，避免与业务事务竞争
- **记录内容**：用户 ID、用户名、操作方法、资源类型、资源 ID、请求路径、IP 地址

---

## 6. 协作流程可视化编辑器

### 6.1 数据模型

```
Collaboration (1) ──→ (N) CollaborationNode
                  ──→ (N) CollaborationEdge

CollaborationNode:
  - node_type: start | end | agent | condition | parallel_gateway
  - agent_id: FK → Agent (仅 agent 类型)
  - config_json: 条件/网关配置 JSON
  - position_x, position_y: 画布坐标

CollaborationEdge:
  - source_node_id, target_node_id: FK → CollaborationNode
  - edge_type: default | success | failure | conditional
  - condition_json: 条件表达式
```

### 6.2 前端编辑器架构

```
┌─────────────────────────────────────────────────┐
│  Toolbar: 保存 / 启动 / 停止 / 返回             │
├────────┬──────────────────────────┬──────────────┤
│ 节点面板 │      Vue Flow 画布       │   属性面板   │
│ (拖拽源) │  Background + Controls   │ (选中编辑)   │
│         │  + MiniMap + SnapGrid    │              │
│ · 开始   │                          │ · 标签       │
│ · 结束   │   ┌───┐    ┌───┐        │ · Agent选择  │
│ · 条件   │   │ S ├───→│ A │        │ · 配置JSON   │
│ · 并行   │   └───┘    └─┬─┘        │ · 边类型     │
│ · Agent列│              ↓          │              │
│   表     │           ┌───┐         │              │
│         │           │ E │         │              │
│         │           └───┘         │              │
└────────┴──────────────────────────┴──────────────┘
```

**交互流程**：
1. **拖拽创建**：从左侧面板拖拽节点 → `onDrop` 计算画布坐标 → `POST /nodes` → 添加到画布
2. **连线**：拖拽 Handle → `onConnect` → `POST /edges` → 画布渲染边
3. **属性编辑**：点击节点/边 → 右侧面板显示属性 → 修改后 `PUT /nodes/{id}` 或 `PUT /edges/{id}`
4. **布局保存**：点击保存 → 收集所有节点坐标 + 视口状态 → `PUT /layout` 批量更新

### 6.3 自定义节点组件

`AgentNode.vue` 根据 `node_type` 显示不同图标和边框样式：

| 节点类型 | 图标 | 边框颜色 |
|---------|------|---------|
| start | VideoPlay | 绿色实线 |
| end | CircleClose | 红色实线 |
| agent | UserFilled | 蓝色实线 |
| condition | Switch | 橙色虚线 |
| parallel_gateway | Connection | 蓝色点线 |

---

## 7. 输出管理增强

### 7.1 FTS5 搜索实现

```python
# 1. FTS 匹配获取排序后的 rowid 列表
fts_sql = "SELECT rowid, rank FROM outputs_fts WHERE outputs_fts MATCH :q ORDER BY rank"

# 2. 用 ORM 加载完整对象（含关联）
query = select(Output).options(selectinload(...)).where(Output.id.in_(row_ids))

# 3. 按 FTS rank 排序恢复顺序
item_map = {item.id: item for item in items}
data = [_output_to_dict(item_map[rid]) for rid in row_ids if rid in item_map]
```

### 7.2 代码高亮

```javascript
// 使用 highlight.js 自动检测语言
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const highlighted = item.content_type
  ? hljs.highlight(content, { language: item.content_type })
  : hljs.highlightAuto(content)
```

### 7.3 批量操作

- **批量删除**：`POST /outputs/batch-delete` + `{ids: [1,2,3]}` → 单次最多 100 条
- **批量导出**：`POST /outputs/batch-export` → 返回 JSON 数组，前端生成下载文件

---

## 8. 前端架构

### 8.1 HTTP 客户端封装

```javascript
const api = axios.create({ baseURL: '/api/v1', timeout: 30000 })

// 请求拦截：自动注入 JWT token
api.interceptors.request.use(config => {
    const token = localStorage.getItem('token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// 响应拦截：业务错误统一提示，401 跳转登录
api.interceptors.response.use(
    response => response.data.code === 200 ? response.data : Promise.reject(response.data),
    error => { /* 网络错误处理 */ }
)
```

### 8.2 路由守卫

```javascript
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    if (to.meta.public) { next(); return }
    if (!token) { next('/login'); return }
    // 基于角色的访问控制
    if (to.meta.roles) {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        if (user && to.meta.roles.includes(user.role)) next()
        else { ElMessage.error('权限不足'); next(from.fullPath || '/dashboard') }
    } else { next() }
})
```

系统设置页面通过 `meta: { roles: ['admin'] }` 限制仅管理员访问。

### 8.3 状态管理

使用 Pinia 管理用户登录状态，侧栏折叠等 UI 状态存储在组件本地。

---

## 9. 部署方案

### Docker Compose 双服务架构

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["./data:/app/data"]      # SQLite 数据持久化
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]

  frontend:
    build: ./frontend                  # 多阶段: node build → nginx serve
    ports: ["80:80"]
    depends_on:
      backend: { condition: service_healthy }
```

### Nginx 配置要点

```nginx
# SPA 路由兜底
location / {
    try_files $uri $uri/ /index.html;
}

# API 反向代理
location /api/ {
    proxy_pass http://backend:8000/api/;
}
```

---

## 10. 测试策略

### 集成测试（85 个用例）

采用 **curl + bash** 端到端测试，覆盖完整业务链路：

```
认证登录 → 未认证访问拒绝验证
→ 创建实例 → 创建供应商 → 更新供应商 → 创建模型 → 创建 Agent → 绑定技能
→ 创建输出 → FTS 搜索 → 批量操作
→ 创建协作 → 添加节点/边 → 保存布局 → 启停控制 → 保存为模板
→ 创建记忆池 → 绑定 Agent
→ Dashboard 概览 / 趋势 / 状态 / 类型分布 / 实例健康
→ 系统信息 / 审计日志 / 用户管理
→ 清理 + 404 验证
```

所有受保护端点的测试均携带 `Authorization: Bearer $TOKEN` 头。每个用例检查响应中的关键字段匹配，失败时输出完整响应体辅助排查。

---

## 附录：关键依赖版本清单

### 后端

| 包 | 版本 |
|---|---|
| fastapi | 0.128.8 |
| sqlalchemy | 2.0.47 |
| aiosqlite | 0.22.1 |
| pydantic | 2.12.5 |
| uvicorn | 0.39.0 |
| python-jose | 3.5.0 |
| bcrypt | 4.0.1 |
| loguru | 0.7.3 |
| alembic | 1.16.5 |

### 前端

| 包 | 版本 |
|---|---|
| vue | 3.5.13 |
| element-plus | 2.13.3 |
| @vue-flow/core | 1.48.2 |
| axios | 1.13.6 |
| highlight.js | 11.11.1 |
| marked | 17.0.3 |
| echarts | 5.6.0 |
| vue-echarts | 7.0.3 |
| vite | 6.3.5 |
