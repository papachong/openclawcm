# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenClawCM is a unified management platform for multi-instance AI agents. It provides a centralized web console for managing OpenClaw instances, agents, collaboration workflows, outputs, and shared memory pools.

## Development Commands

### Local Development

```bash
# Backend (from project root)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (new terminal, from project root)
cd frontend
npm install
npm run dev
```

- Frontend dev server: http://localhost:5173
- Backend API: http://localhost:8000
- Default credentials: `admin / admin123`

### Docker

```bash
docker compose up -d          # Start all services
docker compose up -d --build  # Rebuild and start
```

### Testing

```bash
# Run integration tests (requires running backend)
bash tests/integration_test.sh
```

### Frontend Build

```bash
cd frontend
npm run build   # Production build to dist/
npm run preview # Preview production build
```

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Nginx (Port 80)                        │
│         SPA Static Assets  │  /api/ Reverse Proxy         │
└──────────┬─────────────────┴─────────┬───────────────────┘
           │                           │
┌──────────▼──────────┐   ┌────────────▼──────────────────┐
│   Vue 3 Frontend    │   │      FastAPI Backend          │
│  Element Plus UI    │   │  SQLAlchemy Async ORM         │
│  Vue Flow Editor    │   │  JWT Auth + RBAC              │
│  Pinia State Mgmt   │   │  Audit Middleware             │
└─────────────────────┘   └────────────┬──────────────────┘
                                       │
                          ┌────────────▼──────────────────┐
                          │   SQLite (FTS5) / MySQL       │
                          └───────────────────────────────┘
```

## Backend Structure

```
backend/app/
├── main.py              # FastAPI entrypoint, lifespan, CORS
├── config.py            # Pydantic settings from .env
├── database.py          # Async engine, session, FTS5 setup
├── api/
│   ├── deps.py          # Dependencies (get_db, require_auth)
│   └── v1/
│       ├── router.py    # Aggregates all module routers
│       ├── auth.py      # JWT login, user CRUD
│       ├── instances.py # Instance management + health check
│       ├── models.py    # Model providers + configs
│       ├── agents.py    # Agent CRUD + start/stop + skill binding
│       ├── skills.py    # Skill CRUD + install/uninstall
│       ├── outputs.py   # Output CRUD + FTS search + batch ops
│       ├── collaborations.py  # Flow + nodes + edges + layout
│       ├── memory_pools.py    # Shared memory CRUD + agent binding
│       ├── dashboard.py       # Statistics + charts data
│       └── system.py    # System info + audit logs
├── models/              # SQLAlchemy ORM models (15 models)
├── schemas/             # Pydantic request/response schemas
├── middleware/audit.py  # Auto-logs all write operations
└── utils/
    ├── auth.py          # JWT + bcrypt password hashing
    └── response.py      # Unified response format helpers
```

## Frontend Structure

```
frontend/src/
├── main.js              # App entrypoint
├── App.vue              # Root component
├── api/
│   ├── request.js       # Axios instance with interceptors
│   └── index.js         # All API methods by domain
├── router/index.js      # Vue Router with auth guards
├── stores/              # Pinia state management
├── layouts/MainLayout.vue  # Sidebar + header layout
├── views/               # Page components by domain
│   ├── dashboard/       # ECharts visualizations
│   ├── instances/       # Instance CRUD + health
│   ├── agents/          # Agent management
│   ├── collaborations/  # Flow list + editor
│   │   └── editor/      # Vue Flow DAG editor
│   ├── outputs/         # Output list + FTS search
│   ├── memory-pools/    # Shared memory management
│   ├── models/          # Model provider/config management
│   ├── skills/          # Skill management
│   ├── settings/        # User management (admin only)
│   └── login/           # Authentication
└── i18n/                # Internationalization (en-US, zh-CN)
```

## Key Patterns

### Backend: Unified Response Format

All API responses use this format:
```python
{"code": 200, "message": "success", "data": {...}}
{"code": 400/401/404, "message": "error description", "data": None}
```

Use helpers from `app/utils/response.py`: `success()`, `error()`, `page_response()`

### Backend: Authentication

All routes except `/auth/login` require JWT via `require_auth` dependency:
```python
api_router.include_router(xxx.router, dependencies=[Depends(require_auth)])
```

### Backend: Async ORM with Eager Loading

Always use `selectinload` to avoid N+1 queries:
```python
query = select(Output).options(
    selectinload(Output.instance),
    selectinload(Output.agent),
)
```

### Frontend: API Layer

All API calls go through `src/api/index.js` which exports domain-specific API objects:
```javascript
import { agentApi, instanceApi } from '@/api'
const res = await agentApi.list({ page: 1, page_size: 10 })
```

### Frontend: Route Guards

Routes use `meta.roles` for RBAC. Settings page is admin-only via `meta: { roles: ['admin'] }`.

## Database

- Default: SQLite with WAL mode + FTS5 full-text search on outputs
- Production: MySQL via `DATABASE_URL=mysql+aiomysql://...`
- 17 tables including FTS virtual table
- Models inherit `TimestampMixin` for auto `created_at`/`updated_at`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/openclawcm.db` | Database connection |
| `SECRET_KEY` | `openclawcm-secret-key-change-in-production` | JWT signing secret |
| `CORS_ORIGINS` | `["http://localhost:5173",...]` | Allowed CORS origins |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token expiry (24h) |

## RBAC Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access + user management + audit logs |
| `operator` | Business operations (instances, agents, etc.) |
| `viewer` | Read-only access |
