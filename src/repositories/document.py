from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(
        self,
        user_id: UUID,
    ):
        result = await self.session.execute(
            select(Document).where(
                Document.user_id == user_id,
            )
        )

        return result.scalars().all()

    async def get_by_id(self, user_id: UUID, document_id: UUID):
        result = await self.session.execute(
            select(Document).where(
                (Document.id == document_id), (Document.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        user_id: UUID,
        name: str,
    ) -> Document | None:
        result = await self.session.execute(
            select(Document).where(
                Document.user_id == user_id,
                Document.name == name,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_content_hash(
        self,
        user_id: UUID,
        content_hash: str,
    ) -> Document | None:
        result = await self.session.execute(
            select(Document).where(
                Document.user_id == user_id,
                Document.content_hash == content_hash,
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        document: Document,
    ) -> Document:
        self.session.add(document)

        await self.session.flush()

        return document

    async def get_by_doc_id(self, document_id: UUID):
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )

        return result.scalar_one_or_none()
