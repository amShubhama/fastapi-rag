from fastapi import FastAPI, Request
from src.core.exceptions import AppException
from src.core.exception_handlers import (
    app_exception_handler,
    unhandled_exception_handler,
)
from src.api.routes import v1_router
from src.core.lifespan import lifespan
import time
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="AI RAG API", lifespan=lifespan)

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{process_time:.2f} ms"
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_credentials=True,
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Process-Time"],
    )

    @app.get("/api", tags=["Health"])
    def check_api():
        return {"status": "ok"}

    app.include_router(prefix="/api", router=v1_router)

    return app


app = create_app()
