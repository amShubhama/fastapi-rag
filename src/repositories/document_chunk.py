from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import DocumentChunk, Document, DocumentStatus


class DocumentChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def similarity_search(
        self,
        user_id: UUID,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[DocumentChunk]:

        distance = DocumentChunk.embedding.cosine_distance(query_embedding).label(
            "distance"
        )

        result = await self.session.execute(
            select(DocumentChunk, distance)
            .join(DocumentChunk.document)
            .options(selectinload(DocumentChunk.document))
            .where(
                Document.user_id == user_id,
                Document.status == DocumentStatus.COMPLETED,
            )
            .order_by(distance)
            .limit(limit)
        )

        return result.scalars().all()

    async def keyword_search(
        self,
        user_id: UUID,
        query: str,
        limit: int = 30,
    ) -> list[DocumentChunk]:

        search_query = func.websearch_to_tsquery(
            "english",
            query,
        )

        keyword_score = func.ts_rank_cd(
            DocumentChunk.search_vector,
            search_query,
        ).label("keyword_score")

        result = await self.session.execute(
            select(
                DocumentChunk,
                keyword_score,
            )
            .join(DocumentChunk.document)
            .options(selectinload(DocumentChunk.document))
            .where(
                Document.user_id == user_id,
                Document.status == DocumentStatus.COMPLETED,
                DocumentChunk.search_vector.op("@@")(search_query),
            )
            .order_by(keyword_score.desc())
            .limit(limit)
        )

        return result.scalars().all()
