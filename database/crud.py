"""CRUD operations for database models."""

import json
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from .models import Conversation, Document, Message, User


# ─── User ────────────────────────────────────────────────────────────────────

def create_user(db: Session, username: str, email: str, hashed_password: str) -> User:
    user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


# ─── Conversation ────────────────────────────────────────────────────────────

def create_conversation(db: Session, user_id: int, title: str = "新对话") -> Conversation:
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversations(db: Session, user_id: int) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(desc(Conversation.updated_at))
        .all()
    )


def get_conversation(db: Session, conv_id: int, user_id: int) -> Optional[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.user_id == user_id)
        .first()
    )


def update_conversation_title(db: Session, conv_id: int, user_id: int, title: str) -> Optional[Conversation]:
    conv = get_conversation(db, conv_id, user_id)
    if conv:
        conv.title = title
        db.commit()
        db.refresh(conv)
    return conv


def delete_conversation(db: Session, conv_id: int, user_id: int) -> bool:
    conv = get_conversation(db, conv_id, user_id)
    if conv:
        db.delete(conv)
        db.commit()
        return True
    return False


# ─── Message ─────────────────────────────────────────────────────────────────

def create_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    sources: Optional[list[dict]] = None,
) -> Message:
    sources_json = json.dumps(sources, ensure_ascii=False) if sources else None
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=sources_json,
    )
    db.add(msg)

    # Update conversation timestamp
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv:
        from datetime import datetime, timezone
        conv.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(msg)
    return msg


def get_messages(db: Session, conversation_id: int) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )


def get_recent_messages(db: Session, conversation_id: int, limit: int = 10) -> list[Message]:
    """Get recent messages for chat history context."""
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(desc(Message.created_at))
        .limit(limit)
        .all()
    )


# ─── Document ────────────────────────────────────────────────────────────────

def create_document(
    db: Session,
    user_id: int,
    doc_id: str,
    filename: str,
    page_count: int = 0,
    chunk_count: int = 0,
    summary: Optional[str] = None,
    content_preview: Optional[str] = None,
    file_path: Optional[str] = None,
    conversation_id: Optional[int] = None,
) -> Document:
    doc = Document(
        user_id=user_id,
        doc_id=doc_id,
        filename=filename,
        file_path=file_path,
        page_count=page_count,
        chunk_count=chunk_count,
        summary=summary,
        content_preview=content_preview,
        conversation_id=conversation_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_documents_by_user(db: Session, user_id: int) -> list[Document]:
    return db.query(Document).filter(Document.user_id == user_id).all()


def get_document_by_doc_id(db: Session, doc_id: str) -> Optional[Document]:
    return db.query(Document).filter(Document.doc_id == doc_id).first()


def delete_document(db: Session, doc_id: str, user_id: int) -> bool:
    doc = db.query(Document).filter(Document.doc_id == doc_id, Document.user_id == user_id).first()
    if doc:
        db.delete(doc)
        db.commit()
        return True
    return False
