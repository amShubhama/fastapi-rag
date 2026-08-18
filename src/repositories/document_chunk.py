from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import DocumentChunk, Document, DocumentStatus


class DocumentChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def similarity_search(
        self,
        user_id: UUID,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:

        distance = DocumentChunk.embedding.cosine_distance(query_embedding).label(
            "distance"
        )

        result = await self.session.execute(
            select(DocumentChunk, distance)
            .join(DocumentChunk.document)
            .where(
                Document.user_id == user_id,
                Document.status == DocumentStatus.COMPLETED,
            )
            .order_by(distance)
            .limit(limit)
        )

        results = []

        for row, distance_value in result.all():
            row.distance = distance_value
            row.score = 1.0 - float(distance_value)
            results.append(row)

        return results
