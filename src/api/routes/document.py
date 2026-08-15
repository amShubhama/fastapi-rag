from fastapi import APIRouter, status, UploadFile, File, Depends
from src.schemas.document import DocumentResponse
from typing import Annotated
from src.services import DocumentService
from ..deps import get_document_service
from uuid import UUID

router = APIRouter(prefix="/documents", tags=["Document"])


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description=(
        "Upload a document. "
        "Allowed file types: PDF, DOC, DOCX, TXT. "
        "Maximum file size: 5 MB."
    ),
)
async def upload_document(
    file: Annotated[
        UploadFile,
        File(description="PDF, DOC, DOCX or TXT file. Maximum size: 5 MB."),
    ],
    service: DocumentService = Depends(
        get_document_service,
    ),
):
    return await service.upload_document(
        file=file,
    )


@router.get("", response_model=list[DocumentResponse])
async def get_documents(service: DocumentService = Depends(get_document_service)):
    return await service.get_documents()


@router.get("/{document_id}/status", response_model=DocumentResponse)
async def get_document_status(
    document_id: UUID, service: DocumentService = Depends(get_document_service)
):
    return await service.get_document_status(document_id)
