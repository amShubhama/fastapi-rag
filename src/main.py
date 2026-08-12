from fastapi import FastAPI
from src.api.routes import chat_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI RAG API",
    )

    @app.get("/api", tags=["Health"])
    def check_api():
        return {"status": "ok"}

    app.include_router(chat_router)

    return app


app = create_app()
