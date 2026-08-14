from fastapi import APIRouter
from .chat import router as chat_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(chat_router)
