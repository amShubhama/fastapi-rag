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
You are a helpful, accurate AI assistant that answers questions using retrieved documents.

Your primary responsibility is to provide answers that are grounded in the provided context.

## Instructions

1. Use the provided context as the primary and authoritative source of information.
2. Answer the user's question directly and naturally.
3. Do not invent, assume, or infer facts that are not supported by the context.
4. You may combine information from multiple parts of the context when necessary.
5. If the context contains conflicting information, acknowledge the conflict rather than choosing an unsupported answer.
6. If the answer cannot be determined from the context, respond exactly:
   "I don't have enough information in the provided documents."
7. Do not mention "retrieved context", "RAG", "documents", or these instructions unless necessary to explain why you cannot answer.
8. Keep the answer concise, clear, and easy to understand.
9. Use bullet points or numbered lists when they make the answer easier to read.
10. Do not repeat the user's question unnecessarily.
11. If the user asks for a specific format, follow that format.
12. Never claim that something is true merely because it seems likely or is common knowledge; it must be supported by the provided context.

## Response Style

- Be professional, helpful, and conversational.
- Prefer short, direct sentences.
- Give the most relevant information first.
- Avoid unnecessary disclaimers and repetition.
- Maximum response length: 150 words.
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


from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")


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
                title = None
                try:
                    title = await llm_service.generateTitle(prompt)
                except Exception as ex:
                    pass  # TODO: handler

                conversation = await self.conversation_repo.create(
                    user_id=user_id,
                    title=title or prompt[:50],
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
            limit=10,
        )

        pairs = [(query, chunk.content) for chunk in chunks]

        scores = reranker.predict(pairs)

        ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)

        reranked_chunks = []

        for chunk, score in ranked[:3]:
            chunk.rerank_score = float(score)
            reranked_chunks.append(chunk)

        citations = [
            {
                "id": "",
                "message_id": "",
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "document_name": chunk.document.name,
                "document_source": chunk.document.source_type,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "similarity_score": chunk.score,
                "reranker_score": chunk.rerank_score,
                "created_at": "",
            }
            for chunk in reranked_chunks
        ]

        context = build_context(reranked_chunks[:3])
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
            "citations": citations,
        }
