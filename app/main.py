"""
Synapse - Self-hosted AI backend for Cursor/Cline/Continue
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat, memory, documents, health
from app.core.config import settings
from app.core.database import init_db
from app.core.services import ServiceManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Synapse...")
    
    # Initialize database
    await init_db()
    
    # Initialize services
    app.state.services = ServiceManager()
    await app.state.services.initialize()
    
    print("✅ Synapse is ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Synapse...")
    await app.state.services.shutdown()


# Create FastAPI app
app = FastAPI(
    title="Synapse",
    description="Self-hosted AI backend with persistent memory",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(chat.router, prefix="/v1", tags=["chat"])
app.include_router(memory.router, prefix="/api", tags=["memory"])
app.include_router(documents.router, prefix="/api", tags=["documents"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """OpenAI-compatible error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "invalid_request_error",
                "code": exc.status_code,
            }
        },
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Synapse",
        "version": "0.1.0",
        "description": "Self-hosted AI backend for Cursor/Cline/Continue",
        "endpoints": {
            "openai_compatible": "/v1/chat/completions",
            "documents": "/api/documents",
            "memory": "/api/memory",
            "health": "/health",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )