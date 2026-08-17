import hashlib
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    DocumentTooLargeError,
    DuplicateContentError,
    DuplicateDocumentError,
    InvalidDocumentError,
    DocumentNotFoundError,
)
from src.models.document import (
    Document,
    DocumentSource,
    DocumentStatus,
)
from src.repositories.document import DocumentRepository
from src.storage.document import DocumentStorage
from src.validators.document import DocumentValidator
from src.core.config import settings

from src.ingestion.tasks import (
    ingest_document,
)

user_id = settings.user_id


class DocumentService:
    MAX_FILE_SIZE = 5 * 1024 * 1024
    CHUNK_SIZE = 1024 * 1024

    def __init__(
        self,
        session: AsyncSession,
        document_repo: DocumentRepository,
        document_storage: DocumentStorage,
        document_validator: DocumentValidator,
    ):
        self.session = session
        self.document_repo = document_repo
        self.document_storage = document_storage
        self.document_validator = document_validator

    async def upload_document(
        self,
        file: UploadFile,
    ) -> Document:
        if not file or not file.filename:
            raise InvalidDocumentError()

        filename = self.document_validator.validate_filename(file.filename)

        extension = self.document_validator.get_extension(filename)

        existing = await self.document_repo.get_by_name(
            user_id=user_id,
            name=filename,
        )

        if existing:
            raise DuplicateDocumentError()

        temp_path = self.document_storage.create_temp_path()
        final_path: Path | None = None

        try:
            file_size, content_hash = await self._write_and_hash(
                file=file,
                temp_path=temp_path,
            )

            detected_mime = self.document_validator.validate(
                path=temp_path,
                filename=filename,
            )

            existing = await self.document_repo.get_by_content_hash(
                user_id=user_id,
                content_hash=content_hash,
            )

            if existing:
                raise DuplicateContentError()

            final_path, stored_filename = self.document_storage.create_final_path(
                user_id=user_id,
                extension=extension,
            )

            document = Document(
                user_id=user_id,
                name=filename,
                source_type=DocumentSource.UPLOAD,
                source_uri=None,
                mime_type=detected_mime,
                status=DocumentStatus.PENDING,
                stored_filename=stored_filename,
                storage_path=(self.document_storage.to_storage_path(final_path)),
                document_type=extension.removeprefix("."),
                content_hash=content_hash,
                file_size=file_size,
            )

            await self.document_repo.create(document)

            self.document_storage.finalize(
                temp_path=temp_path,
                final_path=final_path,
            )

            await self.session.commit()

            ingest_document.delay(str(document.id))

            return document

        except IntegrityError as exc:
            await self.session.rollback()

            if final_path is not None:
                self.document_storage.delete(final_path)

            self.document_storage.delete(temp_path)

            raise DuplicateDocumentError() from exc

        except Exception:
            await self.session.rollback()

            if final_path is not None:
                self.document_storage.delete(final_path)

            self.document_storage.delete(temp_path)

            raise

        finally:
            await file.close()

    async def _write_and_hash(
        self,
        file: UploadFile,
        temp_path: Path,
    ) -> tuple[int, str]:
        hasher = hashlib.sha256()
        total_size = 0

        with temp_path.open("wb") as output:
            while True:
                chunk = await file.read(self.CHUNK_SIZE)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > self.MAX_FILE_SIZE:
                    raise DocumentTooLargeError()

                hasher.update(chunk)
                output.write(chunk)

        return total_size, hasher.hexdigest()

    async def get_documents(self):
        return await self.document_repo.get_by_user_id(user_id=user_id)

    async def get_document_status(self, document_id: UUID):
        document = await self.document_repo.get_by_id(
            user_id=user_id, document_id=document_id
        )
        if not document:
            raise DocumentNotFoundError()
        return document
