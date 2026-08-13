from fastapi import APIRouter, Depends, status
from src.services import ChatService
from ..deps import get_chat_service
from src.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationListResponse,
    MessageListResponse,
)
from uuid import UUID

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    req_body: ChatRequest, service: ChatService = Depends(get_chat_service)
):
    return await service.create_chat(req_body.conversation_id, req_body.prompt)


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_conversations(
    service: ChatService = Depends(get_chat_service),
):
    return await service.get_conversations()


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_chats(
    conversation_id: UUID, service: ChatService = Depends(get_chat_service)
):
    return await service.get_chats(conversation_id)
