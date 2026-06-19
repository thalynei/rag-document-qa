from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class DocumentEntry:
    doc_id: str
    doc_name: str
    page_count: int
    chunk_count: int
    doc_summary: str
    uploaded_at: str = ""

    def __post_init__(self):
        if not self.uploaded_at:
            self.uploaded_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ProcessingTask:
    task_id: str
    filename: str
    status: str = "pending"  # pending, processing, completed, failed
    progress: str = ""  # loading, splitting, summarizing, embedding, complete
    error: str | None = None
    doc_id: str | None = None
    result: dict | None = None
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class TempFileContent:
    """临时文件内容（仅当前会话有效）"""
    filename: str
    content: str
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class UserData:
    """用户级别的共享数据（知识库文档、向量库）- 所有对话共享"""
    user_id: int
    documents: dict[str, DocumentEntry] = field(default_factory=dict)
    vectorstore: object = None
    qa_chain: object = None
    upload_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


@dataclass
class SessionData:
    """会话级别的数据（任务、临时文件）- 仅当前会话有效"""
    session_id: str
    tasks: dict[str, ProcessingTask] = field(default_factory=dict)
    temp_files: dict[str, TempFileContent] = field(default_factory=dict)


class UserStore:
    """管理用户级别的共享数据（知识库）"""

    def __init__(self) -> None:
        self._users: dict[int, UserData] = {}

    def get_or_create(self, user_id: int) -> tuple[UserData, bool]:
        if user_id in self._users:
            return self._users[user_id], False
        user_data = UserData(user_id=user_id)
        self._users[user_id] = user_data
        return user_data, True

    def get(self, user_id: int) -> UserData | None:
        return self._users.get(user_id)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}

    def get_or_create(self, session_id: str | None) -> tuple[SessionData, bool]:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id], False
        sid = str(uuid4())
        session = SessionData(session_id=sid)
        self._sessions[sid] = session
        return session, True

    def get(self, session_id: str | None) -> SessionData | None:
        """Return session if it exists, None otherwise (no auto-create)."""
        if not session_id:
            return None
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def find_task(self, task_id: str) -> ProcessingTask | None:
        for session in self._sessions.values():
            if task_id in session.tasks:
                return session.tasks[task_id]
        return None


store = SessionStore()
user_store = UserStore()
