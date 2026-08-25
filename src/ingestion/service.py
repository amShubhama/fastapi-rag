from datetime import datetime, timezone
import logging
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.ingestion.chunking.text import DocumentChunker
from src.ingestion.embeddings.huggingface import EmbeddingService
from src.ingestion.loaders.langchain_document import DocumentLoader
from src.models import Document, DocumentChunk, DocumentStatus
from src.repositories import DocumentRepository
from src.storage.document import DocumentStorage

logger = logging.getLogger(__name__)
import asyncio


class DocumentIngestionService:
    """
    Orchestrates the document ingestion pipeline.

    Pipeline:
        stored file
            ↓
        document loader
            ↓
        extracted pages
            ↓
        text chunks
            ↓
        embeddings
            ↓
        DocumentChunk rows
            ↓
        document = COMPLETED
    """

    def __init__(
        self,
        session: AsyncSession,
        document_storage: DocumentStorage,
        document_loader: DocumentLoader,
        document_chunker: DocumentChunker,
        embedding_service: EmbeddingService,
        document_repo: DocumentRepository,
    ):
        self.session = session
        self.document_storage = document_storage
        self.document_loader = document_loader
        self.document_chunker = document_chunker
        self.embedding_service = embedding_service
        self.document_repo = document_repo

    async def ingest(
        self,
        document_id: UUID,
    ) -> Document:
        document = await self.document_repo.get_by_doc_id(
            document_id=document_id,
        )

        if not document:
            raise ValueError(f"Document not found: {document_id}")

        if document.status == DocumentStatus.COMPLETED:
            return document

        # Update document status to processing
        if document.status != DocumentStatus.PROCESSING:
            document.status = DocumentStatus.PROCESSING
            document.error_message = None
            await self.session.commit()

        try:

            self._validate_document(document)

            file_path = self.document_storage.resolve(document.storage_path)

            if not file_path.exists() or not file_path.is_file():
                raise FileNotFoundError(f"Document file not found at path: {file_path}")

            logger.info(f"Loading document content for ID: {document_id}")

            pages = await asyncio.to_thread(
                self.document_loader.load,
                file_path=str(file_path),
                document_type=document.document_type,
            )

            # Filter empty pages
            pages = [p for p in pages if p.page_content and p.page_content.strip()]

            if not pages:
                raise ValueError("Document contains no extractable text")

            chunks = await asyncio.to_thread(self.document_chunker.split, pages)

            chunks = [
                chunk
                for chunk in chunks
                if chunk.page_content and chunk.page_content.strip()
            ]

            if not chunks:
                raise ValueError("No text chunks were generated.")

            texts = [chunk.page_content for chunk in chunks]

            embeddings = await asyncio.to_thread(
                self.embedding_service.embed_documents, texts
            )

            if len(embeddings) != len(chunks):
                raise ValueError("Embedding count does not match chunk count.")

            # delete document_chunks for this document id (idempotency)
            await self.session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )

            for chunk_index, (
                chunk,
                embedding,
            ) in enumerate(
                zip(
                    chunks,
                    embeddings,
                )
            ):
                page = self._get_page_number(chunk.metadata)

                db_chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk_index,
                    content=chunk.page_content,
                    page_start=page,
                    page_end=page,
                    embedding=embedding,
                )

                self.session.add(db_chunk)

            # mark document completed
            document.status = DocumentStatus.COMPLETED
            document.error_message = None
            document.processed_at = datetime.now(timezone.utc)

            await self.session.commit()
            logger.info(
                f"Successfully finished ingestion for document ID: {document_id}"
            )
            return document

        except Exception as exc:
            logger.error(
                f"Ingestion failed for document {document_id}: {exc}", exc_info=True
            )
            await self.session.rollback()

            try:
                document = await self.document_repo.get_by_doc_id(
                    document_id=document_id
                )
                if document:
                    document.status = DocumentStatus.FAILED
                    document.error_message = self._format_error(exc)
                    await self.session.commit()
            except Exception as inner_exc:
                logger.critical(
                    f"Failed to persist error state for doc {document_id}: {inner_exc}"
                )

            raise

    @staticmethod
    def _validate_document(
        document: Document,
    ) -> None:
        if not document.storage_path:
            raise ValueError("Document has no storage path.")

        if not document.document_type:
            raise ValueError("Document has no document type.")

        supported_types = {"pdf", "txt"}

        if document.document_type.lower() not in supported_types:
            raise ValueError(f"Unsupported document type: {document.document_type}")

    @staticmethod
    def _get_page_number(
        metadata: dict,
    ) -> int | None:
        page = metadata.get("page")

        if page is None:
            return None

        try:
            return int(page) + 1
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _format_error(
        error: Exception,
    ) -> str:
        message = str(error).strip()

        if not message:
            message = error.__class__.__name__

        return message[:4000]
