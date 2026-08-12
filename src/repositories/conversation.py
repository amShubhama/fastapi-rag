from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, con_id):
        query = select(Conversation).where(Conversation.id == con_id)
        result = await self.session.execute(
            query
        )
        return result.one_or_none()
