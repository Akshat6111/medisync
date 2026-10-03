from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.ai.service import chat, clear_session_cache
from app.db.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


class ChatMessageItem(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Text content of the message")


class ChatRequest(BaseModel):
    message: str = Field(..., description="Current user query")
    history: Optional[List[ChatMessageItem]] = Field(
        default=None,
        description="Recent session conversation history for multi-turn context (capped to last 6-8 messages)",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Client session identifier used to cache patient and vectorstore context across turns",
    )


class ChatClearRequest(BaseModel):
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier to invalidate from server cache",
    )


@router.post("/chat")
async def chat_ai(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history_dicts = [h.model_dump() for h in request.history] if request.history else []

    response = await run_in_threadpool(
        chat,
        query=request.message,
        db=db,
        current_user=current_user,
        history=history_dicts,
        session_id=request.session_id,
    )

    return {
        "response": response
    }


@router.post("/chat/clear")
async def clear_chat(
    request: Optional[ChatClearRequest] = None,
    current_user: User = Depends(get_current_user),
):
    session_id = request.session_id if request else None
    clear_session_cache(session_id=session_id, user_id=current_user.id)
    return {"status": "cleared", "session_id": session_id}