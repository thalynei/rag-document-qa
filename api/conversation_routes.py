"""Conversation management routes."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.crud import (
    create_conversation,
    create_message,
    delete_conversation,
    delete_message,
    get_conversation,
    get_conversations,
    get_messages,
    update_conversation_title,
)

from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class CreateConversationRequest(BaseModel):
    title: str = "新对话"


class UpdateTitleRequest(BaseModel):
    title: str


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("")
async def list_conversations(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get all conversations for current user."""
    conversations = get_conversations(db, user.id)
    return [c.to_dict() for c in conversations]


@router.post("")
async def create_new_conversation(
    body: CreateConversationRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new conversation."""
    conv = create_conversation(db, user.id, body.title)
    return conv.to_dict()


@router.get("/{conv_id}")
async def get_conversation_detail(
    conv_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get conversation with messages."""
    conv = get_conversation(db, conv_id, user.id)
    if not conv:
        raise HTTPException(404, "对话不存在")

    messages = get_messages(db, conv_id)
    result = conv.to_dict()
    result["messages"] = [m.to_dict() for m in messages]
    return result


@router.patch("/{conv_id}")
async def update_title(
    conv_id: int,
    body: UpdateTitleRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update conversation title."""
    conv = update_conversation_title(db, conv_id, user.id, body.title)
    if not conv:
        raise HTTPException(404, "对话不存在")
    return conv.to_dict()


@router.delete("/{conv_id}")
async def delete_conv(
    conv_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Delete a conversation."""
    if not delete_conversation(db, conv_id, user.id):
        raise HTTPException(404, "对话不存在")
    return {"status": "deleted"}


@router.delete("/{conv_id}/messages/{message_id}")
async def delete_message_endpoint(
    conv_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """删除单条消息"""
    conv = get_conversation(db, conv_id, user.id)
    if not conv:
        raise HTTPException(404, "对话不存在")
    if not delete_message(db, message_id, conv_id):
        raise HTTPException(404, "消息不存在")
    return {"status": "deleted"}
