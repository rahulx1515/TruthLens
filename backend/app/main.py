"""
TruthLens - Backend Entry Point
FastAPI application with CORS, route registration, and database initialization.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.database.session import Base, engine
import app.models  # ensure models are registered with Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on application startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI-Powered News Credibility & Fake News Detection Platform",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
if "*" not in origins and "http://localhost:5173" not in origins:
    origins.extend(["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "healthy",
        "service": "TruthLens Backend API",
        "version": settings.PROJECT_VERSION,
        "docs_url": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "database": "connected",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

