from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.models.document import DocumentSource, DocumentStatus


class DocumentResponse(BaseModel):
    id: UUID
    name: str
    source_type: DocumentSource
    mime_type: str | None
    status: DocumentStatus
    file_size: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
