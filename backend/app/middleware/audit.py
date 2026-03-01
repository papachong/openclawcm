"""
Audit middleware - automatically logs write operations (POST/PUT/DELETE).
Uses background task to avoid SQLite locking issues.
"""
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from jose import JWTError, jwt

from app.config import settings
from app.database import async_session
from app.models.user import AuditLog


# Map URL path segments to resource types
RESOURCE_MAP = {
    "instances": "instance",
    "models": "model_config",
    "providers": "model_provider",
    "agents": "agent",
    "skills": "skill",
    "outputs": "output",
    "collaborations": "collaboration",
    "auth": "user",
    "system": "system",
}


async def _write_audit_log(username, action, resource_type, resource_id, detail, ip_address):
    """Write audit log in a separate task after a short delay to avoid DB lock."""
    await asyncio.sleep(0.5)  # Wait for main request transaction to commit
    try:
        async with async_session() as session:
            log = AuditLog(
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                detail=detail,
                ip_address=ip_address,
            )
            session.add(log)
            await session.commit()
    except Exception:
        pass


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Only audit write operations
        if request.method not in ("POST", "PUT", "DELETE"):
            return await call_next(request)

        # Skip health check
        if request.url.path == "/health":
            return await call_next(request)

        response = await call_next(request)

        # Only log successful operations (2xx)
        if not (200 <= response.status_code < 300):
            return response

        # Extract user info from JWT token
        username = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                username = payload.get("sub")
            except JWTError:
                pass

        # Determine action and resource
        path_parts = request.url.path.strip("/").split("/")
        action = {
            "POST": "create",
            "PUT": "update",
            "DELETE": "delete",
        }.get(request.method, request.method.lower())

        resource_type = None
        resource_id = None
        for part in path_parts:
            if part in RESOURCE_MAP:
                resource_type = RESOURCE_MAP[part]
            elif part.isdigit() and resource_type:
                resource_id = int(part)

        # Special action detection
        for keyword in ["login", "start", "stop", "restart", "install", "uninstall", "favorite", "copy"]:
            if keyword in path_parts:
                action = keyword
                break

        ip_address = request.client.host if request.client else None

        # Fire-and-forget background task
        asyncio.create_task(_write_audit_log(
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=f"{request.method} {request.url.path}",
            ip_address=ip_address,
        ))

        return response
