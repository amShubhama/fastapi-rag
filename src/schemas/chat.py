import uuid

from datetime import datetime
from pydantic import BaseModel

from src.models import MessageRole


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID | None = None
    prompt: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    user_message: MessageResponse
    assistant_message: MessageResponse


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]


class MessageListResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[MessageResponse]
