from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Message, MessageRole
from uuid import UUID
from sqlalchemy import select


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conversation_id: UUID, role: MessageRole, content: str):
        message = Message(conversation_id=conversation_id, role=role, content=content)
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_by_conversation_id(self, conversation_id: UUID):
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return result.scalars().all()
