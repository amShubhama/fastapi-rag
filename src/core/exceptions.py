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
