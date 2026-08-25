import asyncio
import logging
from uuid import UUID

from celery.schedules import crontab
from sqlalchemy import select

from src.db.session import sessionLocal
from src.ingestion.chunking.text import DocumentChunker
from src.ingestion.embeddings.huggingface import EmbeddingService
from src.ingestion.loaders.langchain_document import DocumentLoader
from src.ingestion.service import DocumentIngestionService
from src.models import Document, DocumentStatus
from src.repositories import DocumentRepository
from src.storage.document import DocumentStorage
from src.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

_embeddings_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingService(model_name="BAAI/bge-small-en-v1.5")
    return _embeddings_service


@celery_app.task(
    bind=True,
    name="documents.ingest",
    acks_late=True,
    reject_on_worker_lost=True,
    autoretry_for=(Exception,),
    dont_autoretry_for=(ValueError,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def ingest_document(
    self,
    document_id: str,
) -> None:

    async def run() -> None:
        storage = DocumentStorage()

        loader = DocumentLoader()

        chunker = DocumentChunker(
            chunk_size=1000,
            chunk_overlap=150,
        )

        embeddings = get_embedding_service()

        async with sessionLocal() as session:

            service = DocumentIngestionService(
                session=session,
                document_storage=storage,
                document_loader=loader,
                document_chunker=chunker,
                embedding_service=embeddings,
                document_repo=DocumentRepository(session=session),
            )

            await service.ingest(UUID(document_id))

    try:
        asyncio.run(run())
    except Exception as exc:
        logger.error(f"Task retry triggered for document {document_id} due to: {exc}")
        raise self.retry(exc=exc)


celery_app.conf.beat_schedule = {
    "ingest-document-publisher-beat": {
        "task": "documents.ingest_publisher",
        "schedule": crontab(minute="*/1"),
    }
}


@celery_app.task(name="documents.ingest_publisher", acks_late=True)
def ingest_document_publisher() -> str:

    async def run() -> str:
        async with sessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    select(Document)
                    .where(Document.status == DocumentStatus.PENDING)
                    .limit(5)
                    .with_for_update(skip_locked=True)
                )

                documents = result.scalars().all()
                if not documents:
                    return "No pending documents found for ingestion"

                for document in documents:
                    document.status = DocumentStatus.PROCESSING
                    session.add(document)

            for document in documents:
                ingest_document.delay(str(document.id))
                logger.info(
                    f"Dispatched for ingestion -> doc_id: {document.id}, doc_name: {document.name}"
                )

        return f"Successfully dispatched {len(documents)} documents"

    return asyncio.run(run())
