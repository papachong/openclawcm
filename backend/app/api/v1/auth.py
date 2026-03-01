"""
Authentication API endpoints - login, register, password management, user CRUD.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.utils.auth import (
    verify_password, get_password_hash, create_access_token,
    require_auth, require_admin,
)
from app.utils.response import success, error

router = APIRouter()


# ==================== Schemas ====================
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: str = "operator"


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== Auth Endpoints ====================
@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        return error("用户名或密码错误", 401)

    if not user.is_active:
        return error("账户已被禁用", 403)

    token = create_access_token(data={"sub": user.username, "role": user.role})
    return success({
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "email": user.email,
        }
    }, "登录成功")


@router.get("/me")
async def get_current_user_info(user: User = Depends(require_auth)):
    return success({
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
        "email": user.email,
    })


@router.put("/password")
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.old_password, user.password_hash):
        return error("原密码错误", 400)

    user.password_hash = get_password_hash(data.new_password)
    await db.flush()
    return success(None, "密码修改成功")


# ==================== User Management (Admin) ====================
@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(select(func.count(User.id)))
    total = total_result.scalar() or 0

    result = await db.execute(
        select(User).order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()
    data = [{
        "id": u.id,
        "username": u.username,
        "display_name": u.display_name,
        "role": u.role,
        "email": u.email,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    } for u in items]

    return success({"items": data, "total": total, "page": page, "page_size": page_size})


@router.post("/users")
async def create_user(
    data: RegisterRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Check duplicate
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        return error("用户名已存在", 400)

    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        display_name=data.display_name,
        email=data.email,
        role=data.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return success({
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }, "用户创建成功")


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return error("用户不存在", 404)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

    await db.flush()
    return success({"id": user.id, "username": user.username}, "更新成功")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return error("用户不存在", 404)

    if user.role == "admin":
        # Check if this is the last admin
        admin_count = await db.execute(
            select(func.count(User.id)).where(User.role == "admin")
        )
        if (admin_count.scalar() or 0) <= 1:
            return error("不能删除最后一个管理员", 400)

    await db.delete(user)
    return success(None, "删除成功")
