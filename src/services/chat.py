from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.repositories import (
    ConversationRepository,
    MessageRepository,
    DocumentChunkRepository,
)
from src.models import MessageRole, MessageCitation
from .llm import LLMService
from src.core.config import settings
from uuid import UUID
from src.core.exceptions import ConversationNotFoundError, LLMServiceError
from src.static.prompts import RAG_SYSTEM_PROMPT, CHAT_SYSTEM_PROMPT
from sentence_transformers import CrossEncoder
from src.schemas.chat import CitationResponse
from src.helpers.helper import build_query_with_context, build_context
from src.ingestion.tasks import embeddings

user_id: UUID = UUID(settings.user_id)
llm_service = LLMService(ollama_url=settings.ollama_url, model=settings.model)
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

            chat_messages = [
                {
                    "role": "system",
                    "content": CHAT_SYSTEM_PROMPT,
                }
            ]

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
        try:
            if conversation_id:
                conversation = await self.conversation_repo.get_by_id(
                    user_id=user_id, con_id=conversation_id
                )

                if not conversation:
                    raise ConversationNotFoundError()

            else:
                title = None
                try:
                    title = await llm_service.generateTitle(query)
                except Exception as ex:
                    pass  # TODO: handler

                conversation = await self.conversation_repo.create(
                    user_id=user_id,
                    title=title or query[:50],
                )

            # Get the previous messages
            messages = await self.message_repo.get_by_conversation_id(conversation.id)

            query_embedding = embeddings.embed_query(query)

            chunks = await self.document_chunk_repo.similarity_search(
                user_id=user_id,
                query_embedding=query_embedding,
                limit=20,
            )

            pairs = [(query, chunk.content) for chunk in chunks]

            scores = reranker.predict(pairs)

            ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)

            chat_messages = [
                {
                    "role": "system",
                    "content": RAG_SYSTEM_PROMPT,
                }
            ]

            # conversation context
            for message in messages:
                chat_messages.append(
                    {
                        "role": message.role,
                        "content": message.content,
                    }
                )

            context = build_context(ranked[:5])
            query_with_context = build_query_with_context(query, context)

            chat_messages.append(
                {
                    "role": "user",
                    "content": query_with_context,
                }
            )

            try:
                llm_response = await llm_service.generate(
                    messages=chat_messages,
                )
            except Exception:
                raise LLMServiceError()

            user_message = await self.message_repo.create(
                conversation.id,
                MessageRole.USER,
                query,
            )

            assistant_message = await self.message_repo.create(
                conversation.id,
                MessageRole.ASSISTANT,
                llm_response,
            )

            citations = [
                MessageCitation(
                    message_id=assistant_message.id,
                    chunk=chunk,
                    score=score,
                )
                for chunk, score in ranked[:5]
            ]

            self.session.add_all(citations)

            await self.session.flush()

            citation_responses = [
                CitationResponse(
                    id=citation.id,
                    message_id=citation.message_id,
                    document_id=citation.chunk.document.id,
                    document_name=citation.chunk.document.name,
                    document_source=citation.chunk.document.source_type,
                    page_start=citation.chunk.page_start,
                    page_end=citation.chunk.page_end,
                    score=citation.score,
                    created_at=citation.created_at,
                )
                for citation in citations
            ]
            await self.session.commit()
            return {
                "conversation": conversation,
                "user_message": user_message,
                "llm_response": {
                    "assistant_message": assistant_message,
                    "citations": citation_responses,
                },
            }
        except Exception:
            await self.session.rollback()
            raise
