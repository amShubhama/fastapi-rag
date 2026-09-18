import uuid

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from src.models import MessageRole


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID | None = None
    prompt: str = Field(..., min_length=1, max_length=1000)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("prompt must not be empty")

        return value


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


class CitationResponse(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    document_source: str
    page_start: int | None
    page_end: int | None
    score: float
    created_at: datetime
