"""Authentication routes and JWT utilities."""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database.connection import get_db
from database.crud import create_user, get_user_by_email, get_user_by_id, get_user_by_username

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "rag-qa-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: Optional[str] = None


# ─── Utils ───────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ─── Dependencies ────────────────────────────────────────────────────────────

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user from JWT token (header or cookie)."""

    token = None

    # Try Authorization header first
    if credentials:
        token = credentials.credentials

    # Fallback to cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="未登录")

    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token 无效")

    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    # Validate input
    if len(body.username) < 2 or len(body.username) > 50:
        raise HTTPException(400, "用户名长度需在 2-50 之间")
    if len(body.password) < 6:
        raise HTTPException(400, "密码长度至少 6 位")

    # Check duplicates
    if get_user_by_username(db, body.username):
        raise HTTPException(409, "用户名已存在")
    if get_user_by_email(db, body.email):
        raise HTTPException(409, "邮箱已被注册")

    # Create user
    user = create_user(db, body.username, body.email, hash_password(body.password))

    # Generate token
    token = create_access_token({"sub": str(user.id)})
    response.set_cookie("access_token", token, httponly=True, max_age=7 * 24 * 3600)

    # 初始化用户的 session
    await _init_user_session(request, response, user, db)

    return TokenResponse(
        access_token=token,
        user=user.to_dict(),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    # Find user (by username or email)
    user = get_user_by_username(db, body.username)
    if not user:
        user = get_user_by_email(db, body.username)

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "用户名或密码错误")

    # Generate token
    token = create_access_token({"sub": str(user.id)})
    response.set_cookie("access_token", token, httponly=True, max_age=7 * 24 * 3600)

    # 初始化用户的 session（加载向量库）
    await _init_user_session(request, response, user, db)

    return TokenResponse(
        access_token=token,
        user=user.to_dict(),
    )


async def _init_user_session(request: Request, response: Response, user, db: Session):
    """初始化用户的 session，加载文档和向量库到 user_store（用户级别共享数据）"""
    try:
        from .session import store, user_store, DocumentEntry
        from database.crud import get_documents_by_user
        from rag.retriever import get_retriever
        from rag.chain import create_qa_chain
        from rag.embeddings import get_embeddings
        from rag.embeddings import load_vectorstore

        # 获取或创建 session（会话级别）
        session_id = request.cookies.get("session_id")
        session, is_new = store.get_or_create(session_id)
        if is_new:
            response.set_cookie("session_id", session.session_id, httponly=True)

        # 获取或创建用户级别共享数据
        user_data, _ = user_store.get_or_create(user.id)

        # 从数据库加载用户的文档
        user_docs = get_documents_by_user(db, user.id)
        logger.info(f"用户 {user.username} 有 {len(user_docs)} 个文档")

        # 清空旧的文档列表，重新加载
        user_data.documents.clear()

        # 加载文档信息到 user_data
        for doc in user_docs:
            user_data.documents[doc.doc_id] = DocumentEntry(
                doc_id=doc.doc_id,
                doc_name=doc.filename,
                page_count=doc.page_count,
                chunk_count=doc.chunk_count,
                doc_summary=doc.summary or "",
            )

        # 尝试加载已有的向量库（使用用户专属集合）
        try:
            from rag.embeddings import get_user_collection_name
            collection_name = get_user_collection_name(user.id)
            embeddings = get_embeddings()
            vectorstore = load_vectorstore(embeddings, collection_name=collection_name)

            if vectorstore:
                user_data.vectorstore = vectorstore
                retriever = get_retriever(vectorstore)
                user_data.qa_chain = create_qa_chain(retriever)
                logger.info(f"已加载用户 {user.username} 的 {len(user_docs)} 个文档和向量库")
            else:
                logger.warning("向量库为空，无法创建 QA chain")
                user_data.vectorstore = None
                user_data.qa_chain = None
        except Exception as e:
            logger.warning(f"加载向量库失败: {e}")
            user_data.vectorstore = None
            user_data.qa_chain = None
    except Exception as e:
        logger.warning(f"初始化 session 失败: {e}")


@router.get("/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user)):
    """Get current user info (requires auth)."""
    return UserResponse(**user.to_dict())


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "ok"}


# ─── Password Change ────────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if len(body.new_password) < 6:
        raise HTTPException(400, "新密码长度至少 6 位")
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(400, "当前密码错误")
    from database.crud import update_user_password
    update_user_password(db, user.id, hash_password(body.new_password))
    return {"status": "ok", "message": "密码修改成功"}


# ─── Avatar Upload ──────────────────────────────────────────────────────────

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import os
    from pathlib import Path

    # 验证文件类型
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(400, "仅支持 JPG/PNG/WebP/GIF 格式")

    # 验证文件大小（最大 2MB）
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(400, "头像文件大小不能超过 2MB")

    # 保存文件
    avatars_dir = Path(__file__).parent.parent / "uploads" / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(file.filename or ".jpg")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        ext = ".jpg"
    filename = f"{user.id}{ext}"
    file_path = avatars_dir / filename

    with open(file_path, "wb") as f:
        f.write(content)

    # 更新数据库
    from database.crud import update_user_avatar
    update_user_avatar(db, user.id, filename)

    return {
        "status": "ok",
        "avatar_url": f"/uploads/avatars/{filename}",
    }


# ─── User Settings ──────────────────────────────────────────────────────────

@router.get("/settings")
async def get_settings(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from database.crud import get_or_create_user_settings
    settings = get_or_create_user_settings(db, user.id)
    return {"system_prompt": settings.system_prompt or ""}


class UpdateSettingsRequest(BaseModel):
    system_prompt: str | None = None


@router.put("/settings")
async def update_settings(
    body: UpdateSettingsRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from database.crud import update_system_prompt
    if body.system_prompt is not None:
        update_system_prompt(db, user.id, body.system_prompt)
    return {"status": "ok"}
