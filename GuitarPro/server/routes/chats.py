from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.models import Chat, ChatMessage, MessageRole, User
from server import schemas
from server.auth import get_current_user
from server.dependencies import get_db

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/", response_model=schemas.ChatList)
def list_chats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id)
        .order_by(Chat.created_at.desc())
        .all()
    )


@router.post("/", response_model=schemas.ChatRead, status_code=status.HTTP_201_CREATED)
def create_chat(payload: schemas.ChatCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    title = (payload.title or "Новый чат").strip() or "Новый чат"
    chat = Chat(user_id=current_user.id, title=title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.put("/{chat_id}", response_model=schemas.ChatRead)
def rename_chat(chat_id: int, payload: schemas.ChatUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.get(Chat, chat_id)
    if chat is None or chat.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Чат не найден")
    chat.title = payload.title.strip()
    db.commit()
    db.refresh(chat)
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.get(Chat, chat_id)
    if chat is None or chat.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Чат не найден")
    db.delete(chat)
    db.commit()


@router.get("/{chat_id}/messages", response_model=schemas.MessageList)
def list_messages(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.get(Chat, chat_id)
    if chat is None or chat.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Чат не найден")
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


@router.post("/{chat_id}/messages", response_model=schemas.MessageRead, status_code=status.HTTP_201_CREATED)
def add_message(chat_id: int, payload: schemas.MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.get(Chat, chat_id)
    if chat is None or chat.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Чат не найден")
    message = ChatMessage(chat_id=chat_id, role=MessageRole(payload.role), content=payload.content.strip())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
