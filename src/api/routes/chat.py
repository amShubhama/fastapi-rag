from fastapi import APIRouter,Depends
from src.services.chat_service import ChatService
from ..deps import get_chat_service


router = APIRouter(
  prefix='/chat',
  tags=['Chat']
)

@router.get('/{conversation_id}/messages')
async def get_chats(conversation_id:int, service:ChatService=Depends(get_chat_service)):
  data = await service.get_chats(conversation_id)
  print(data)
  return {'data':"data"}