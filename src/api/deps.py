from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.repositories import (
    ConversationRepository,
    MessageRepository,
    DocumentRepository,
)
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


from src.services import DocumentService
from src.storage.document import DocumentStorage
from src.validators.document import DocumentValidator


def get_document_repository(
    session: AsyncSession = Depends(get_db),
) -> DocumentRepository:
    return DocumentRepository(session=session)


def get_document_service(
    session: AsyncSession = Depends(get_db),
    document_repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentService:
    validator = DocumentValidator()
    storage = DocumentStorage()
    return DocumentService(
        session=session,
        document_repo=document_repo,
        document_validator=validator,
        document_storage=storage,
    )
