from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Initialize database
from database.connection import init_db  # noqa: E402

init_db()

app = FastAPI(title="RAG Document QA", version="2.0.0")

# CORS origins: configurable via CORS_ORIGINS env var (comma-separated)
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
cors_origins = os.getenv("CORS_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .auth import router as auth_router  # noqa: E402
from .conversation_routes import router as conv_router  # noqa: E402
from .routes import router  # noqa: E402

app.include_router(auth_router)
app.include_router(conv_router)
app.include_router(router, prefix="/api")

# 静态文件服务：上传文件（头像等）
uploads_dir = Path(__file__).parent.parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
from fastapi.staticfiles import StaticFiles  # noqa: E402

app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
