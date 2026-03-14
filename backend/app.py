from fastapi import FastAPI

from backend.api.routes import router as api_router


app = FastAPI(
    title="AI Repository Agent Backend",
    description="Phase 1 backend scaffold for repository analysis orchestration.",
    version="0.1.0",
)

app.include_router(api_router)
