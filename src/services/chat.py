from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.repositories import (
    ConversationRepository,
    MessageRepository,
    DocumentChunkRepository,
)
from src.models import MessageRole
from .llm import LLMService
from src.core.config import settings
from uuid import UUID
from src.core.exceptions import ConversationNotFoundError, LLMServiceError

llm_service = LLMService(ollama_url=settings.ollama_url, model=settings.model)

SYSTEM_PROMPT = """
                You are a helpful AI assistant.

                Answer questions clearly and accurately in max 50 words.
                If you don't know the answer, say so.
                Do not make up information.
            """

CONTEXT_SYSTEM_PROMPT = """
You are a helpful AI assistant.

Answer the user's question using the provided context.

Rules:
- Use the provided context as the primary source of truth.
- Do not make up information.
- If the answer is not present in the context, say:
  "I don't have enough information in the provided documents."
- Answer clearly and accurately in max 50 words.
"""


def build_context(chunks) -> str:
    """
    Build the context passed to the LLM from the
    most relevant document chunks.
    """

    if not chunks:
        return "No relevant context was found."

    return "\n\n".join(
        f"[Document Chunk {index}]\n{chunk.content}"
        for index, chunk in enumerate(chunks, start=1)
    )


user_id: UUID = UUID(settings.user_id)
from src.ingestion.tasks import embeddings


class ChatService:
    def __init__(
        self,
        session: AsyncSession,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        document_chunk_repo: DocumentChunkRepository,
    ):
        self.session = session
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.document_chunk_repo = document_chunk_repo

    async def create_chat(
        self,
        conversation_id: UUID | None,
        prompt: str,
    ):
        try:

            if conversation_id:
                conversation = await self.conversation_repo.get_by_id(
                    con_id=conversation_id, user_id=user_id
                )

                if not conversation:
                    raise ConversationNotFoundError()

            else:

                conversation = await self.conversation_repo.create(
                    user_id=user_id,
                    title=prompt[:50],
                )

            user_message = await self.message_repo.create(
                conversation.id,
                MessageRole.USER,
                prompt,
            )

            # Get the previous messages
            messages = await self.message_repo.get_by_conversation_id(conversation.id)

            chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            chat_messages.extend(
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in messages
            )

            try:
                llm_response = await llm_service.generate(messages=chat_messages)
            except Exception as ex:
                raise LLMServiceError()

            assistant_message = await self.message_repo.create(
                conversation.id,
                MessageRole.ASSISTANT,
                llm_response,
            )

            await self.session.commit()

            return {
                "conversation_id": conversation.id,
                "user_message": user_message,
                "assistant_message": assistant_message,
            }
        except Exception as ex:
            await self.session.rollback()
            raise

    async def get_conversations(self):
        conversations = await self.conversation_repo.get_by_user_id(user_id)
        return {"conversations": conversations}

    async def get_chats(self, conversation_id: UUID):

        conversation = await self.conversation_repo.get_by_id(
            con_id=conversation_id, user_id=user_id
        )

        if not conversation:
            raise ConversationNotFoundError()

        messages = await self.message_repo.get_by_conversation_id(conversation.id)

        return {"conversation": conversation, "messages": messages}

    async def create_chat_with_context(self, conversation_id: UUID | None, query: str):
        query_embedding = embeddings.embed_query(query)
        chunks = await self.document_chunk_repo.similarity_search(
            user_id=user_id,
            query_embedding=query_embedding,
            limit=5,
        )

        context = build_context(chunks)
        chat_messages = [
            {
                "role": "system",
                "content": CONTEXT_SYSTEM_PROMPT,
            }
        ]
        chat_messages.append(
            {
                "role": MessageRole.USER,
                "content": f"""
                    Context:
                    --------------------
                    {context}
                    --------------------

                    Question:
                    {query}
                """,
            }
        )
        llm_response = await llm_service.generate(messages=chat_messages)
        return {
            "llm_response": llm_response,
            "retrieved_chunks": chunks,
        }
