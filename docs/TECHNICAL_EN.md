# OpenClawCM Technical Documentation

> This document provides a concise overview of key technical implementations in OpenClawCM for developers looking to understand the system internals.

---

## 1. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend Framework | Vue 3 (Composition API) | 3.5 |
| UI Library | Element Plus | 2.13 |
| Flow Editor | @vue-flow/core + background/controls/minimap | 1.48 |
| Code Highlighting | highlight.js | 11.11 |
| Markdown Rendering | marked | 17.0 |
| Data Visualization | ECharts + vue-echarts | 5.6 / 7.0 |
| Build Tool | Vite | 6.4 |
| Backend Framework | FastAPI | 0.128 |
| ORM | SQLAlchemy 2.0 (async) | 2.0.47 |
| Database | SQLite (aiosqlite) / MySQL (aiomysql) | — |
| Authentication | python-jose (JWT HS256) + bcrypt | — |
| Deployment | Docker Compose (Nginx + uvicorn) | — |

---

## 2. Database Design

### 2.1 Async Engine Initialization

```python
# database.py
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)
```

- SQLite configured with **WAL mode** (`PRAGMA journal_mode=WAL`) for improved concurrent read/write performance
- Seamless switch to MySQL in production by changing `DATABASE_URL`

### 2.2 Data Model Overview (15 Models, 17 Tables)

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

SystemSetting (Key-Value config table)
```

All models inherit `TimestampMixin`, automatically maintaining `created_at` / `updated_at`.

### 2.3 FTS5 Full-Text Search

```python
# Virtual table created on startup
CREATE VIRTUAL TABLE IF NOT EXISTS outputs_fts
USING fts5(title, summary, content, content=outputs, content_rowid=id);

# Triggers keep FTS index in sync with the outputs table
CREATE TRIGGER outputs_ai AFTER INSERT ON outputs BEGIN
    INSERT INTO outputs_fts(rowid, title, summary, content)
    VALUES (new.id, new.title, new.summary, new.content);
END;
```

Queries use `MATCH` + `rank` ordering: first retrieve FTS rowid list, then load full ORM objects with `IN` clause (including relationships) to avoid N+1 problems.

---

## 3. Authentication & Authorization

### 3.1 JWT Flow

```
Client POST /api/v1/auth/login {username, password}
    → bcrypt.checkpw(password, stored_hash)
    → jose.jwt.encode({sub: user_id, username, role}, SECRET_KEY, HS256)
    → Returns {token, user} (24h expiry)

Subsequent requests Header: Authorization: Bearer <token>
    → require_auth dependency decodes and validates
    → require_admin additionally checks role == "admin"
```

### 3.2 Password Security

Direct `bcrypt` hashing with cost factor 12 (default), no passlib intermediate layer.

### 3.3 Role Permissions

| Role | Permissions |
|------|-------------|
| `admin` | Full read/write + user management + audit log access |
| `operator` | Business operations on instances/agents/flows |
| `viewer` | Read-only access |

### 3.4 Route-Level Authentication

All API routers (except auth) enforce authentication via router-level `dependencies`:

```python
# router.py
api_router.include_router(instances.router, prefix="/instances",
                          dependencies=[Depends(require_auth)])
# auth router has no dependency — login is a public endpoint
api_router.include_router(auth.router, prefix="/auth")
```

Requests without a valid token receive `{"detail": "Not authenticated"}`.

---

## 4. API Design

### 4.1 Unified Response Format

```python
def success(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}

def error(message, code=400):
    return JSONResponse({"code": code, "message": message, "data": None}, status_code=200)

def page_response(data, total, page, page_size):
    return {"code": 200, "message": "success",
            "data": data, "total": total, "page": page, "page_size": page_size}
```

All APIs return HTTP 200; business errors are distinguished via the `code` field (400/401/404). The frontend interceptor handles errors uniformly based on `code`.

### 4.2 Preventing ORM Lazy Loading

Async ORM does not support implicit lazy loading. All queries needing related data use `selectinload`:

```python
query = select(Output).options(
    selectinload(Output.instance),
    selectinload(Output.agent),
    selectinload(Output.tags),
)
```

Response dictionaries are built manually (`_output_to_dict`) using `__dict__` inspection to avoid triggering unloaded relationship access.

### 4.3 Router Module Breakdown (10 Modules, 89 Endpoints)

| Module | Prefix | Endpoints | Key Features |
|--------|--------|-----------|-------------|
| auth | `/auth` | 7 | JWT login, user CRUD |
| instances | `/instances` | 6 | Instance CRUD + health check |
| models | `/models` | 9 | Provider + model config CRUD |
| agents | `/agents` | 12 | Agent CRUD + start/stop + skill binding + agent_count sync |
| skills | `/skills` | 7 | Skill CRUD + install/uninstall |
| outputs | `/outputs` | 10 | Output CRUD + FTS + tags + batch ops |
| collaborations | `/collaborations` | 19 | Flow + nodes + edges + layout + control + template copy |
| memory-pools | `/memory-pools` | 8 | Memory pool CRUD + agent binding + multi-dimensional filtering (instance/agent/collaboration/keyword) |
| dashboard | `/dashboard` | 7 | Statistics overview + trends + agent stats + output types + instance health |
| system | `/system` | 4 | System info + audit logs |

---

## 5. Audit Middleware

```python
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.method in ("POST", "PUT", "DELETE"):
            # Decode JWT from Authorization header to extract user info
            # Async write to audit_logs table (asyncio.create_task + 0.5s delay to avoid SQLite locks)
        return response
```

- **Zero intrusion**: No manual logging required in business code
- **SQLite lock avoidance**: Audit writes delayed 0.5s to avoid contention with business transactions
- **Recorded fields**: user_id, username, HTTP method, resource_type, resource_id, request path, IP address

---

## 6. Collaboration Visual Flow Editor

### 6.1 Data Model

```
Collaboration (1) ──→ (N) CollaborationNode
                  ──→ (N) CollaborationEdge

CollaborationNode:
  - node_type: start | end | agent | condition | parallel_gateway
  - agent_id: FK → Agent (agent type only)
  - config_json: Condition/gateway configuration JSON
  - position_x, position_y: Canvas coordinates

CollaborationEdge:
  - source_node_id, target_node_id: FK → CollaborationNode
  - edge_type: default | success | failure | conditional
  - condition_json: Condition expression
```

### 6.2 Frontend Editor Architecture

```
┌─────────────────────────────────────────────────┐
│  Toolbar: Save / Start / Stop / Back             │
├────────┬──────────────────────────┬──────────────┤
│  Node  │      Vue Flow Canvas     │  Properties  │
│ Palette│  Background + Controls   │    Panel     │
│ (drag) │  + MiniMap + SnapGrid    │ (selection)  │
│        │                          │              │
│ · Start│   ┌───┐    ┌───┐        │ · Label      │
│ · End  │   │ S ├───→│ A │        │ · Agent pick │
│ · Cond.│   └───┘    └─┬─┘        │ · Config JSON│
│ · Para.│              ↓          │ · Edge type  │
│ · Agent│           ┌───┐         │              │
│   list │           │ E │         │              │
│        │           └───┘         │              │
└────────┴──────────────────────────┴──────────────┘
```

**Interaction Flow**:
1. **Drag to create**: Drag node from palette → `onDrop` calculates canvas position → `POST /nodes` → renders on canvas
2. **Connect**: Drag Handle → `onConnect` → `POST /edges` → renders edge
3. **Edit properties**: Click node/edge → right panel shows properties → on change `PUT /nodes/{id}` or `PUT /edges/{id}`
4. **Save layout**: Click save → collect all node positions + viewport state → `PUT /layout` batch update

### 6.3 Custom Node Component

`AgentNode.vue` renders different icons and border styles based on `node_type`:

| Node Type | Icon | Border |
|-----------|------|--------|
| start | VideoPlay | Green solid |
| end | CircleClose | Red solid |
| agent | UserFilled | Blue solid |
| condition | Switch | Orange dashed |
| parallel_gateway | Connection | Blue dotted |

---

## 7. Output Management Enhancements

### 7.1 FTS5 Search Implementation

```python
# 1. FTS match to get ranked rowid list
fts_sql = "SELECT rowid, rank FROM outputs_fts WHERE outputs_fts MATCH :q ORDER BY rank"

# 2. Load full objects with ORM (including relationships)
query = select(Output).options(selectinload(...)).where(Output.id.in_(row_ids))

# 3. Restore FTS rank ordering
item_map = {item.id: item for item in items}
data = [_output_to_dict(item_map[rid]) for rid in row_ids if rid in item_map]
```

### 7.2 Code Syntax Highlighting

```javascript
// Auto-detect language with highlight.js
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const highlighted = item.content_type
  ? hljs.highlight(content, { language: item.content_type })
  : hljs.highlightAuto(content)
```

### 7.3 Batch Operations

- **Batch delete**: `POST /outputs/batch-delete` + `{ids: [1,2,3]}` → max 100 per request
- **Batch export**: `POST /outputs/batch-export` → returns JSON array, frontend generates downloadable file

---

## 8. Frontend Architecture

### 8.1 HTTP Client Setup

```javascript
const api = axios.create({ baseURL: '/api/v1', timeout: 30000 })

// Request interceptor: auto-inject JWT token
api.interceptors.request.use(config => {
    const token = localStorage.getItem('token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// Response interceptor: unified error handling, 401 redirect to login
api.interceptors.response.use(
    response => response.data.code === 200 ? response.data : Promise.reject(response.data),
    error => { /* Network error handling */ }
)
```

### 8.2 Route Guard

```javascript
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    if (to.meta.public) { next(); return }
    if (!token) { next('/login'); return }
    // Role-based access control
    if (to.meta.roles) {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        if (user && to.meta.roles.includes(user.role)) next()
        else { ElMessage.error('Insufficient permissions'); next(from.fullPath || '/dashboard') }
    } else { next() }
})
```

The Settings page is restricted to admin-only via `meta: { roles: ['admin'] }`.

### 8.3 State Management

Pinia manages user login state. UI states like sidebar collapse are stored locally in components.

---

## 9. Deployment

### Docker Compose Dual-Service Architecture

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["./data:/app/data"]      # SQLite data persistence
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]

  frontend:
    build: ./frontend                  # Multi-stage: node build → nginx serve
    ports: ["80:80"]
    depends_on:
      backend: { condition: service_healthy }
```

### Nginx Configuration Highlights

```nginx
# SPA route fallback
location / {
    try_files $uri $uri/ /index.html;
}

# API reverse proxy
location /api/ {
    proxy_pass http://backend:8000/api/;
}
```

---

## 10. Testing Strategy

### Integration Tests (85 Test Cases)

End-to-end testing using **curl + bash**, covering the full business workflow:

```
Authentication login → Unauthenticated access rejection
→ Create Instance → Create Provider → Update Provider → Create Model → Create Agent → Bind Skills
→ Create Output → FTS Search → Batch Operations
→ Create Collaboration → Add Nodes/Edges → Save Layout → Start/Stop Control → Save as Template
→ Create Memory Pool → Bind Agent
→ Dashboard Overview / Trends / Agent Stats / Output Types / Instance Health
→ System Info / Audit Logs / User Management
→ Cleanup + 404 Validation
```

All protected endpoint tests include `Authorization: Bearer $TOKEN` headers. Each test case verifies key field matches in the response, with full response body output on failure for debugging.

---

## Appendix: Key Dependency Versions

### Backend

| Package | Version |
|---------|---------|
| fastapi | 0.128.8 |
| sqlalchemy | 2.0.47 |
| aiosqlite | 0.22.1 |
| pydantic | 2.12.5 |
| uvicorn | 0.39.0 |
| python-jose | 3.5.0 |
| bcrypt | 4.0.1 |
| loguru | 0.7.3 |
| alembic | 1.16.5 |

### Frontend

| Package | Version |
|---------|---------|
| vue | 3.5.13 |
| element-plus | 2.13.3 |
| @vue-flow/core | 1.48.2 |
| axios | 1.13.6 |
| highlight.js | 11.11.1 |
| marked | 17.0.3 |
| echarts | 5.6.0 |
| vue-echarts | 7.0.3 |
| vite | 6.3.5 |

---

## 11. OpenClaw Gateway Service

OpenClawCM communicates with OpenClaw instances via WebSocket for configuration sync and remote control.

### 11.1 Gateway Communication Protocol

```python
# services/openclaw_gateway.py
async def _gateway_call(instance_url: str, token: str, method: str, params: dict) -> Any:
    ws_url = _to_ws_url(instance_url)  # http:// → ws://
    async with websockets.connect(ws_url, origin=origin) as ws:
        # 1. Send connect request
        connect_req = {
            "type": "req", "id": uuid, "method": "connect",
            "params": {
                "minProtocol": 3, "maxProtocol": 3,
                "client": {"id": "gateway-client", "version": "openclawcm"},
                "role": "operator",
                "scopes": ["operator.read", "operator.admin", "operator.approvals", "operator.pairing"],
                "auth": {"token": token},
            }
        }
        # 2. Wait for connect response
        # 3. Send business request (agents.list, config.get, skills.status, etc.)
        # 4. Return response payload
```

### 11.2 Supported Gateway APIs

| API Method | Function | Return Data |
|------------|----------|-------------|
| `agents.list` | Get agent list | `[{name, role, slug, version, permission}]` |
| `config.get` | Get full configuration | `{models, plugins, gateway, ...}` |
| `skills.status` | Get skill status | `{skills: [{name, description, eligible, ...}]}` |
| `sessions.list` | Get session list | `{sessions: [...]}` |

### 11.3 Instance Configuration Sync

The `sync_instance_config()` function implements full instance synchronization:

```python
async def sync_instance_config(instance_url: str, token: str) -> Dict:
    return {
        "agents": _normalize_agents(await _gateway_call(..., "agents.list", {})),
        "models": _normalize_models(config),      # Extracted from config.get
        "skills": _normalize_skills(await _gateway_call(..., "skills.status", {})),
        "raw_config": actual_config,
        "gateway_version": gw.get("version"),
        "errors": [],  # Collect API call errors
    }
```

**Data Normalization**: Different OpenClaw versions may return different formats. `_normalize_*` functions handle unified processing:
- `_normalize_agents`: Handles `agents` / `id` / `agentId` field variants
- `_normalize_models`: Parses OpenClaw's `providers.{key}.models[]` structure
- `_normalize_skills`: Extracts skill details from `skills.status`

### 11.4 Collaboration Flow Execution

Collaboration flows support remote execution control:

```python
# POST /collaborations/{id}/execute
{
    "status": "running",      # pending → running → completed/failed
    "started_at": "2025-03-05T10:00:00Z",
    "current_node_id": 5,     # Current execution node
    "execution_log": [...]    # Execution log
}
```

Execution flow sends messages to agents via `send_agent_message()`:

```python
async def send_agent_message(instance_url: str, token: str,
                             message: str, session_key: str = None) -> Dict:
    params = {"message": message}
    if session_key:
        params["sessionKey"] = session_key
    return await _gateway_call(instance_url, token, "agent", params)
```

---

## 12. Memory Pool Multi-Dimensional Filtering

Memory pools support filtering by instance, agent, collaboration flow, and keyword:

### 12.1 Backend API

```python
@router.get("")
async def list_memory_pools(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    agent_id: Optional[int] = Query(default=None),      # Filter by Agent
    instance_id: Optional[int] = Query(default=None),   # Filter by instance
    collaboration_id: Optional[int] = Query(default=None),  # Filter by collaboration
    keyword: Optional[str] = Query(default=None),       # Keyword search
    db: AsyncSession = Depends(get_db),
):
```

### 12.2 Join Queries

```python
# Filter by instance_id via Agent association
if instance_id:
    query = query.join(AgentMemoryPoolBinding).join(Agent).filter(
        Agent.instance_id == instance_id
    )

# Filter by collaboration_id directly
if collaboration_id:
    query = query.filter(SharedMemoryPool.collaboration_id == collaboration_id)
```

### 12.3 Frontend Cascading Filter

```javascript
// When instance is selected, Agent dropdown auto-filters
const filteredAgents = computed(() => {
    if (!searchForm.instance_id) return allAgents.value
    return allAgents.value.filter(a => a.instance_id === searchForm.instance_id)
})
```
