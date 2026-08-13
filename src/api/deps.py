from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.repositories import ConversationRepository, MessageRepository
from src.services import ChatService


def get_conversation_repository(
    session: AsyncSession = Depends(get_db),
) -> ConversationRepository:
    return ConversationRepository(session)


def get_message_repository(
    session: AsyncSession = Depends(get_db),
) -> MessageRepository:
    return MessageRepository(session)


def get_chat_service(
    session: AsyncSession = Depends(get_db),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> ChatService:
    return ChatService(
        session=session, conversation_repo=conversation_repo, message_repo=message_repo
    )
