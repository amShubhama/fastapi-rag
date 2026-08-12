from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories import ConversationRepository

class ChatService:
  def __init__(self, session:AsyncSession, conversation_repo:ConversationRepository):
    self.session = session
    self.conversation_repo = conversation_repo

  async def get_chats(self, con_id:str):
    conversation = await self.conversation_repo.get_by_id(con_id)
    return conversation