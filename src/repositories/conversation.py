from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.models import Conversation
from uuid import UUID


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, con_id: UUID, user_id: UUID):
        query = select(Conversation).where(
            # (Conversation.id == con_id) & (Conversation.user_id == user_id)
            # and_((Conversation.id == con_id), (Conversation.user_id == user_id))
            (Conversation.id == con_id),
            (Conversation.user_id == user_id),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_id: UUID, title: str):
        conversation = Conversation(user_id=user_id, title=title)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_by_user_id(self, user_id: UUID):
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
        )
        return result.scalars().all()
