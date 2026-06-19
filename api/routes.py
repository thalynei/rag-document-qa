from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from queue import Empty, Queue
from threading import Thread
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database.connection import get_db
from database.crud import create_document, create_message, delete_document, get_document_by_doc_id, get_documents_by_user, get_messages, get_recent_messages
from rag.loader import load_pdf
from rag.chain import create_direct_chain, create_qa_chain, summarize_document
from rag.embeddings import add_documents_to_vectorstore, create_vectorstore, delete_documents_by_filter, load_vectorstore
from rag.loader import load_pdf
from rag.retriever import get_retriever
from rag.splitter import split_documents

from .auth import get_current_user
from .dependencies import get_cached_embeddings
from .models import (
    ChatRequest,
    ClearResponse,
    DocumentItem,
    StatusResponse,
    UploadResponse,
    UploadStatusResponse,
    UploadTaskResponse,
)
from .session import DocumentEntry, ProcessingTask, TempFileContent, store, user_store

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Strong references to background tasks to prevent GC (BUG #5 fix)
_background_tasks: set[asyncio.Task] = set()


def _format_chat_history_from_db(messages, max_turns: int = 5) -> str:
    """Format chat history from database messages."""
    recent = messages[-(max_turns * 2) :]
    lines = []
    for msg in recent:
        role = "用户" if msg.role == "user" else "助手"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


@router.post("/upload", response_model=UploadTaskResponse)
async def upload_document(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadTaskResponse:
    session_id = request.cookies.get("session_id")
    session, is_new = store.get_or_create(session_id)
    if is_new:
        response.set_cookie("session_id", session.session_id, httponly=True)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, detail="文件大小超过限制（最大 50MB）")

    suffix = os.path.splitext(file.filename or "")[1].lower()
    if suffix not in (".pdf", ".txt", ".md", ".docx"):
        raise HTTPException(415, detail=f"不支持的文件格式: {suffix}")

    # 保存文件到 uploads 目录
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", str(user.id))
    os.makedirs(uploads_dir, exist_ok=True)

    # 使用 doc_id 作为文件名前缀，避免冲突
    doc_id = str(uuid4())
    safe_filename = f"{doc_id}_{file.filename}"
    file_path = os.path.join(uploads_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    task_id = str(uuid4())
    task = ProcessingTask(task_id=task_id, filename=file.filename or "unknown")
    session.tasks[task_id] = task

    # Store strong reference to prevent GC (BUG #5 fix)
    bg_task = asyncio.create_task(
        _process_document(session.session_id, task_id, file_path, file.filename or "unknown", user.id, doc_id, user.id)
    )
    _background_tasks.add(bg_task)
    bg_task.add_done_callback(_background_tasks.discard)

    return UploadTaskResponse(task_id=task_id, filename=file.filename or "unknown", status="processing")


@router.post("/upload/temp")
async def upload_temp_file(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """临时文件上传（仅解析内容，不向量化存储）"""
    session_id = request.cookies.get("session_id")
    session, is_new = store.get_or_create(session_id)
    if is_new:
        response.set_cookie("session_id", session.session_id, httponly=True)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, detail="文件大小超过限制（最大 50MB）")

    suffix = os.path.splitext(file.filename or "")[1].lower()
    if suffix not in (".pdf", ".txt", ".md", ".docx"):
        raise HTTPException(415, detail=f"不支持的文件格式: {suffix}")

    # 保存到临时文件并解析
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 解析文件内容
        docs = await asyncio.to_thread(load_pdf, tmp_path, file.filename or "unknown")
        file_content = "\n\n".join(doc.page_content for doc in docs)

        # 存储到 session 的临时文件中
        temp_id = str(uuid4())
        session.temp_files[temp_id] = TempFileContent(
            filename=file.filename or "unknown",
            content=file_content[:50000],  # 限制最大 50000 字符
        )

        logger.info(f"临时文件已解析: {file.filename}, {len(file_content)} 字符")

        return {
            "temp_id": temp_id,
            "filename": file.filename,
            "content_length": len(file_content),
            "message": "文件已解析，可以开始提问",
        }
    except Exception as e:
        logger.error(f"临时文件解析失败: {e}")
        raise HTTPException(500, detail=f"文件解析失败: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@router.get("/temp/{temp_id}/content")
async def get_temp_file_content(
    temp_id: str,
    request: Request,
):
    """获取临时文件内容"""
    session_id = request.cookies.get("session_id")
    session = store.get(session_id)

    if not session or temp_id not in session.temp_files:
        raise HTTPException(404, detail="临时文件不存在")

    temp_file = session.temp_files[temp_id]
    return {
        "filename": temp_file.filename,
        "content": temp_file.content,
    }


async def _process_document(session_id: str, task_id: str, file_path: str, filename: str, user_id: Optional[int] = None, doc_id: Optional[str] = None, owner_user_id: Optional[int] = None):
    session = store.get(session_id)
    if not session:
        return
    task = session.tasks.get(task_id)
    if not task:
        return

    if not doc_id:
        doc_id = str(uuid4())

    # 获取用户级别的共享数据
    user_data = None
    if owner_user_id:
        user_data, _ = user_store.get_or_create(owner_user_id)

    try:
        task.status = "processing"

        task.progress = "loading"
        docs = await asyncio.to_thread(load_pdf, file_path, filename)
        page_count = len(docs)

        # 提取文档内容预览
        content_preview = "\n\n".join(doc.page_content for doc in docs)[:3000]

        task.progress = "splitting"
        chunks = await asyncio.to_thread(split_documents, docs)
        chunk_count = len(chunks)

        for chunk in chunks:
            chunk.metadata["doc_id"] = doc_id

        task.progress = "summarizing"
        summary = await asyncio.to_thread(summarize_document, docs)

        task.progress = "embedding"
        embeddings = get_cached_embeddings()

        # 使用用户级别的向量库（所有对话共享）
        if user_data:
            async with user_data.upload_lock:
                if user_data.vectorstore is None:
                    user_data.vectorstore = await asyncio.to_thread(
                        create_vectorstore, chunks, embeddings
                    )
                else:
                    await asyncio.to_thread(
                        add_documents_to_vectorstore, user_data.vectorstore, chunks
                    )

                retriever = get_retriever(user_data.vectorstore)
                user_data.qa_chain = create_qa_chain(retriever)

        doc_entry = DocumentEntry(
            doc_id=doc_id,
            doc_name=filename,
            page_count=page_count,
            chunk_count=chunk_count,
            doc_summary=summary,
        )
        if user_data:
            user_data.documents[doc_id] = doc_entry

        # 保存到数据库（包含文件路径）
        if user_id:
            try:
                from database.connection import SessionLocal
                db = SessionLocal()
                try:
                    create_document(
                        db=db,
                        user_id=user_id,
                        doc_id=doc_id,
                        filename=filename,
                        page_count=page_count,
                        chunk_count=chunk_count,
                        summary=summary,
                        content_preview=content_preview,
                        file_path=file_path,
                    )
                    logger.info(f"文档已保存到数据库: {filename}")
                finally:
                    db.close()
            except Exception as e:
                logger.warning(f"保存文档到数据库失败: {e}")

        task.status = "completed"
        task.progress = "complete"
        task.doc_id = doc_id
        task.result = {
            "session_id": session_id,
            "filename": filename,
            "page_count": page_count,
            "chunk_count": chunk_count,
            "summary": summary,
        }
        logger.info(f"文档处理完成: {filename}, {page_count} 页, {chunk_count} 块")
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        logger.error(f"文档处理失败: {filename}, 错误: {e}")


@router.get("/upload/status/{task_id}", response_model=UploadStatusResponse)
async def get_upload_status(task_id: str, request: Request) -> UploadStatusResponse:
    # Use get() to avoid creating orphan sessions (BUG #4 fix)
    session_id = request.cookies.get("session_id")
    session = store.get(session_id)

    task = None
    if session:
        task = session.tasks.get(task_id)
    if not task:
        task = store.find_task(task_id)
    if not task:
        raise HTTPException(404, detail="任务不存在")

    result = None
    if task.status == "completed" and task.result:
        result = UploadResponse(**task.result)

    return UploadStatusResponse(
        task_id=task.task_id,
        filename=task.filename,
        status=task.status,
        progress=task.progress,
        error=task.error,
        result=result,
    )


@router.get("/status", response_model=StatusResponse)
async def get_status(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)) -> StatusResponse:
    # 先从 user_store 获取文档（用户级别的共享数据）
    documents = []
    if user:
        user_data, _ = user_store.get_or_create(user.id)

        # 如果 vectorstore 为 None 但数据库中有文档，自动加载已有的向量库
        if user_data.vectorstore is None:
            from database.crud import get_documents_by_user
            user_docs = get_documents_by_user(db, user.id)
            if user_docs:
                # 尝试加载已有的向量库
                embeddings = get_cached_embeddings()
                user_data.vectorstore = await asyncio.to_thread(load_vectorstore, embeddings)
                if user_data.vectorstore:
                    retriever = get_retriever(user_data.vectorstore)
                    user_data.qa_chain = create_qa_chain(retriever)
                    logger.info(f"自动加载用户 {user.id} 的向量库")

        documents = [
            DocumentItem(
                id=doc.doc_id,
                filename=doc.doc_name,
                page_count=doc.page_count,
                chunk_count=doc.chunk_count,
                summary=doc.doc_summary,
                uploaded_at=doc.uploaded_at,
            )
            for doc in user_data.documents.values()
        ]

    # 如果 user_store 中没有文档，从数据库加载
    if not documents and user:
        from database.crud import get_documents_by_user
        user_docs = get_documents_by_user(db, user.id)
        documents = [
            DocumentItem(
                id=doc.doc_id,
                filename=doc.filename,
                page_count=doc.page_count,
                chunk_count=doc.chunk_count,
                summary=doc.summary or "",
                uploaded_at=doc.created_at.isoformat() if doc.created_at else "",
            )
            for doc in user_docs
        ]

    has_doc = len(documents) > 0
    first = documents[0] if documents else None

    return StatusResponse(
        has_document=has_doc,
        documents=documents,
        filename=first.filename if first else None,
        page_count=first.page_count if first else 0,
        chunk_count=first.chunk_count if first else 0,
        summary=first.summary if first else "",
    )


@router.delete("/document/{doc_id}", response_model=ClearResponse)
async def delete_single_document(doc_id: str, request: Request, user=Depends(get_current_user)) -> ClearResponse:
    # 从用户级别的共享数据中删除文档
    if not user:
        raise HTTPException(401, detail="未登录")

    user_data = user_store.get(user.id)
    if not user_data:
        raise HTTPException(404, detail="用户数据不存在")

    if doc_id not in user_data.documents:
        raise HTTPException(404, detail="文档不存在")

    if user_data.vectorstore:
        delete_documents_by_filter(user_data.vectorstore, {"doc_id": doc_id})

    del user_data.documents[doc_id]

    if user_data.documents:
        retriever = get_retriever(user_data.vectorstore)
        user_data.qa_chain = create_qa_chain(retriever)
    else:
        user_data.vectorstore = None
        user_data.qa_chain = None

    return ClearResponse(status="deleted")


@router.delete("/document", response_model=ClearResponse)
async def clear_document(request: Request) -> ClearResponse:
    session_id = request.cookies.get("session_id")
    if session_id:
        store.delete(session_id)
    return ClearResponse()


@router.post("/chat")
async def chat(
    request: Request,
    body: ChatRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> StreamingResponse:
    # 获取用户级别的共享数据（知识库）
    user_data = None
    if user:
        user_data, _ = user_store.get_or_create(user.id)

        # 如果 vectorstore 为 None，尝试自动加载
        if user_data.vectorstore is None:
            from database.crud import get_documents_by_user
            user_docs = get_documents_by_user(db, user.id)
            if user_docs:
                embeddings = get_cached_embeddings()
                user_data.vectorstore = await asyncio.to_thread(load_vectorstore, embeddings)
                if user_data.vectorstore:
                    retriever = get_retriever(user_data.vectorstore)
                    user_data.qa_chain = create_qa_chain(retriever)

    # 使用用户的 qa_chain（RAG 模式），否则使用直接对话链
    if user_data and user_data.qa_chain:
        chain = user_data.qa_chain
    else:
        chain = create_direct_chain()

    if not body.question.strip():
        raise HTTPException(400, detail="请输入有效问题")

    # Build chat history from DB or request
    if body.conversation_id:
        # Load history from database
        db_messages = get_recent_messages(db, body.conversation_id, limit=10)
        chat_history_str = _format_chat_history_from_db(db_messages)

        # Save user message to DB
        create_message(db, body.conversation_id, "user", body.question)
    else:
        # Use history from request (fallback)
        recent = body.chat_history[-10:]
        lines = []
        for msg in recent:
            role = "用户" if msg.role == "user" else "助手"
            lines.append(f"{role}: {msg.content}")
        chat_history_str = "\n".join(lines)

    # 如果有临时文件，添加到上下文中
    temp_context = ""
    session_id = request.cookies.get("session_id")
    session = store.get(session_id)
    if session and session.temp_files:
        temp_parts = []
        for temp_id, temp_file in session.temp_files.items():
            temp_parts.append(f"## 文件: {temp_file.filename}\n{temp_file.content[:10000]}")
        if temp_parts:
            temp_context = "\n\n## 当前会话上传的临时文件\n" + "\n\n".join(temp_parts)

    # Capture references
    conv_id = body.conversation_id

    # 构建完整的问题（包含临时文件上下文）
    full_question = body.question
    if temp_context:
        full_question = f"{body.question}\n\n---\n请参考以下临时文件内容回答问题：{temp_context}"

    async def event_generator():
        try:
            # Run the entire stream in a thread to avoid blocking the event loop
            def _stream_all():
                chunks_gen, source_docs = chain.stream(
                    {
                        "question": full_question,
                        "chat_history": chat_history_str,
                    }
                )
                chunks = list(chunks_gen)
                return chunks, source_docs

            chunks, source_docs = await asyncio.to_thread(_stream_all)

            for chunk in chunks:
                yield f"event: token\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)

            sources = [
                {
                    "source": f"{doc.metadata.get('source', '未知来源')} - {doc.metadata.get('page_label', '')}",
                    "content": doc.page_content[:200],
                }
                for doc in source_docs
            ]

            # Save assistant message to DB
            if conv_id:
                full_answer = "".join(chunks)
                create_message(db, conv_id, "assistant", full_answer, sources if sources else None)

            yield f"event: done\ndata: {json.dumps({'sources': sources}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"聊天流式生成失败: {e}")
            yield f"event: error\ndata: {json.dumps({'error': '服务内部错误，请稍后重试'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Document Management API ─────────────────────────────────────────────────

@router.get("/documents")
async def list_user_documents(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """获取用户的所有文档"""
    documents = get_documents_by_user(db, user.id)
    return [doc.to_dict() for doc in documents]


@router.get("/documents/{doc_id}")
async def get_document_detail(
    doc_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """获取文档详情（含预览）"""
    doc = get_document_by_doc_id(db, doc_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(404, detail="文档不存在")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "page_count": doc.page_count,
        "chunk_count": doc.chunk_count,
        "summary": doc.summary,
        "content_preview": doc.content_preview,
        "doc_id": doc.doc_id,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.delete("/documents/{doc_id}")
async def delete_user_document(
    doc_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """删除文档（从数据库、向量库和文件系统）"""
    # 获取文档信息
    doc = get_document_by_doc_id(db, doc_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(404, detail="文档不存在")

    # 删除原始文件
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.unlink(doc.file_path)
            logger.info(f"已删除文件: {doc.file_path}")
        except OSError as e:
            logger.warning(f"删除文件失败: {e}")

    # 从数据库删除
    if not delete_document(db, doc_id, user.id):
        raise HTTPException(404, detail="文档不存在")

    # 从用户级别的向量库删除
    user_data = user_store.get(user.id)
    if user_data and user_data.vectorstore:
        try:
            delete_documents_by_filter(user_data.vectorstore, {"doc_id": doc_id})
        except Exception as e:
            logger.warning(f"从向量库删除文档失败: {e}")

    # 从 user_data 中删除
    if user_data and doc_id in user_data.documents:
        del user_data.documents[doc_id]

    return {"status": "deleted"}


@router.get("/documents/{doc_id}/content")
async def get_document_content(
    doc_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """获取文档内容用于预览"""
    doc = get_document_by_doc_id(db, doc_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(404, detail="文档不存在")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(404, detail="文件不存在")

    # 根据文件类型读取内容
    suffix = os.path.splitext(doc.filename)[1].lower()
    content = ""

    try:
        if suffix == ".txt" or suffix == ".md":
            with open(doc.file_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif suffix == ".pdf":
            # 使用 PyPDF 读取
            from rag.loader import load_pdf
            docs = await asyncio.to_thread(load_pdf, doc.file_path, doc.filename)
            content = "\n\n".join(d.page_content for d in docs)
        elif suffix == ".docx":
            # 使用 docx2txt 读取
            import docx2txt
            content = await asyncio.to_thread(docx2txt.process, doc.file_path)
        else:
            content = "不支持预览此文件格式"
    except Exception as e:
        logger.error(f"读取文件内容失败: {e}")
        content = f"读取文件失败: {str(e)}"

    return {
        "filename": doc.filename,
        "content": content[:20000],  # 限制返回内容长度
        "total_length": len(content),
    }
