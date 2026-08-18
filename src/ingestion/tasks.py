import asyncio
from uuid import UUID

from src.ingestion.chunking.text import DocumentChunker
from src.ingestion.embeddings.huggingface import EmbeddingService
from src.ingestion.loaders.langchain_document import DocumentLoader
from src.ingestion.service import DocumentIngestionService
from src.storage.document import DocumentStorage
from src.worker.celery_app import celery_app
from src.db.session import sessionLocal
from src.repositories import DocumentRepository

embeddings = EmbeddingService(
    model_name="BAAI/bge-small-en-v1.5",
)


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
):
    async def run():

        storage = DocumentStorage()

        loader = DocumentLoader()

        chunker = DocumentChunker(
            chunk_size=1000,
            chunk_overlap=150,
        )

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

    asyncio.run(run())
