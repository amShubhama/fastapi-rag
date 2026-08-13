from fastapi import FastAPI
from src.api.routes import chat_router
from src.core.exceptions import AppException
from src.core.exception_handlers import (
    app_exception_handler,
    unhandled_exception_handler,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI RAG API",
    )

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/api", tags=["Health"])
    def check_api():
        return {"status": "ok"}

    app.include_router(chat_router)

    return app


app = create_app()
