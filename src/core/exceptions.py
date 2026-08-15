class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ConversationNotFoundError(AppException):
    def __init__(self):
        super().__init__(
            message="Conversation not found",
            status_code=404,
        )


class LLMServiceError(AppException):
    def __init__(self):
        super().__init__(
            message="Unable to generate a response",
            status_code=502,
        )


class DocumentTooLargeError(AppException):
    def __init__(self):
        super().__init__(
            message="Maximum file size is 5 MB",
            status_code=413,
        )


class DuplicateDocumentError(AppException):
    def __init__(self):
        super().__init__(
            message="A document with this filename already exists",
            status_code=409,
        )


class DuplicateContentError(AppException):
    def __init__(self):
        super().__init__(
            message="A document with the same content already exists",
            status_code=409,
        )


class InvalidDocumentError(AppException):
    def __init__(self, message):
        super().__init__(
            message=message or "A valid document file is required",
            status_code=400,
        )


class DocumentStorageError(AppException):
    def __init__(self):
        super().__init__(
            message="Unable to store the document",
            status_code=500,
        )


class DocumentNotFoundError(AppException):
    def __init__(self):
        super().__init__(message="Document not found", status_code=404)
