from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.config.settings import settings
from app.routes.api_router import api_router
from app.services.connection_manager import connection_manager
from app.services.redis_pubsub import redis_pubsub_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Redis PubSub background listener
    try:
        await redis_pubsub_manager.start_listener(connection_manager)
    except Exception:
        pass
    yield
    # Shutdown: Stop Redis PubSub listener
    try:
        await redis_pubsub_manager.stop_listener()
    except Exception:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Instrument Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": f"{settings.API_V1_STR}/docs",
        "platform_ui": "/platform",
    }


# ---------------------------------------------------------------------------
# Workshop 12 – Simple health probe (no DB / Redis dependency)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health():
    """Lightweight liveness endpoint used by Docker HEALTHCHECK and CD pipeline."""
    return {"status": "ok", "message": "Hello Sakon Nakhon Cloud!"}


@app.get("/platform", response_class=HTMLResponse)
@app.get("/chat", response_class=HTMLResponse)
@app.get("/e2e", response_class=HTMLResponse)
async def get_e2e_client():
    client_path = (
        Path(__file__).resolve().parent.parent / "tests" / "e2e" / "client.html"
    )
    if client_path.exists():
        return HTMLResponse(content=client_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Platform Client not found</h1>", status_code=404)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
