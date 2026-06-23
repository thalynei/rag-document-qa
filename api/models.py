from typing import Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    chat_history: list[ChatMessage] = []
    conversation_id: Optional[int] = None
    model: Optional[str] = None  # 可选：指定使用的模型


class ModelInfo(BaseModel):
    id: str
    display_name: str
    provider: str
    max_tokens: int = 8192
    description: str = ""


class DocumentItem(BaseModel):
    id: str
    filename: str
    page_count: int
    chunk_count: int
    summary: str
    uploaded_at: str


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    page_count: int
    chunk_count: int
    summary: str


class StatusResponse(BaseModel):
    has_document: bool
    documents: list[DocumentItem] = []
    filename: str | None = None
    page_count: int = 0
    chunk_count: int = 0
    summary: str = ""


class SourceInfo(BaseModel):
    source: str
    content: str


class ClearResponse(BaseModel):
    status: str = "cleared"


class UploadTaskResponse(BaseModel):
    task_id: str
    filename: str
    status: str


class UploadStatusResponse(BaseModel):
    task_id: str
    filename: str
    status: str
    progress: str | None = None
    error: str | None = None
    result: UploadResponse | None = None
