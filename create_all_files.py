#!/usr/bin/env python3
"""
Create all Synapse project files automatically
"""
import os
import base64
from pathlib import Path

# Base directory
BASE_DIR = Path(".")

# File contents encoded to avoid issues with quotes and special characters
FILES = {
    ".gitignore": """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Virtual environments
venv/
ENV/
env/
.venv

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store

# Environment variables
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3
postgres_data/

# Logs
logs/
*.log

# Temp files
tmp/
temp/

# Docker
.docker/

# Project specific
data/
uploads/
*.bak
.cache/
node_modules/""",

    "Dockerfile": """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 synapse && chown -R synapse:synapse /app
USER synapse

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]""",

    "docker-compose.yml": """version: '3.8'

services:
  postgres:
    image: ankane/pgvector:v0.5.1
    environment:
      POSTGRES_USER: synapse
      POSTGRES_PASSWORD: synapse_password
      POSTGRES_DB: synapse_db
    volumes:
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U synapse"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  synapse:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://synapse:synapse_password@postgres:5432/synapse_db
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - JWT_SECRET=${JWT_SECRET:-default-secret-change-in-production}
      - API_KEY=${API_KEY:-default-key-change-in-production}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./data:/app/data

  # Optional: Ollama for local models
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    profiles:
      - local

volumes:
  postgres_data:
  redis_data:
  ollama_data:""",

    "requirements.txt": """# Core framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
pgvector==0.2.4
psycopg2-binary==2.9.9

# Redis
redis==5.0.1
aiocache==0.12.2

# AI/ML
langchain==0.1.0
langchain-community==0.1.0
langchain-openai==0.0.3
langchain-anthropic==0.0.1
langchain-litellm==0.0.1
litellm==1.17.0
openai==1.7.0
anthropic==0.8.1

# RAG
r2r==0.2.0

# Memory
mem0ai==0.0.9

# MCP
fastmcp==0.1.0

# Utilities
httpx==0.25.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiofiles==23.2.1
python-dotenv==1.0.0

# Development
pytest==7.4.4
pytest-asyncio==0.23.3
black==23.12.1
ruff==0.1.11
mypy==1.8.0

# Monitoring (optional)
prometheus-client==0.19.0
sentry-sdk==1.39.2""",

    ".env.example": """# Environment
ENVIRONMENT=development

# API Keys (add the ones you need)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
MISTRAL_API_KEY=...
COHERE_API_KEY=...
REPLICATE_API_TOKEN=...
HUGGINGFACE_API_KEY=...

# Database (default for docker-compose)
DATABASE_URL=postgresql://synapse:synapse_password@localhost:5432/synapse_db

# Redis (default for docker-compose)
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=your-super-secret-jwt-key-change-this
API_KEY=your-api-key-for-clients

# Optional: Local models
OLLAMA_HOST=http://localhost:11434

# Optional: OpenRouter for advanced routing
OPENROUTER_API_KEY=...

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Logging
LOG_LEVEL=INFO

# Optional: Monitoring
SENTRY_DSN=
ENABLE_PROMETHEUS=false""",

    "Makefile": """.PHONY: help install dev test lint format clean docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\\033[36m%-15s\\033[0m %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run development server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	pytest tests/ -v

lint: ## Run linter
	ruff check app/ tests/
	mypy app/

format: ## Format code
	black app/ tests/
	ruff check app/ tests/ --fix

clean: ## Clean cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-up: ## Start services with docker-compose
	docker-compose up -d

docker-down: ## Stop services
	docker-compose down

docker-logs: ## Show logs
	docker-compose logs -f

docker-build: ## Build docker image
	docker-compose build

db-migrate: ## Run database migrations
	alembic upgrade head

db-rollback: ## Rollback last migration
	alembic downgrade -1

setup: ## Initial setup
	cp .env.example .env
	@echo "✅ Created .env file. Please edit it with your API keys."
	@echo "📝 Next steps:"
	@echo "   1. Edit .env file with your API keys"
	@echo "   2. Run 'make docker-up' to start services"
	@echo "   3. Visit http://localhost:8000" """,

    "QUICKSTART.md": """# 🚀 Synapse Quick Start Guide

## Prerequisites

- Docker & Docker Compose
- At least one LLM API key (OpenAI, Anthropic, etc.)
- 5 minutes ⏱️

## Step 1: Clone & Setup

```bash
# Clone the repository
git clone https://github.com/eagurin/synapse.git
cd synapse

# Initial setup
make setup
```

## Step 2: Configure API Keys

Edit `.env` file with your API keys:

```bash
# Required: At least one LLM provider
OPENAI_API_KEY=sk-...        # If you have OpenAI
ANTHROPIC_API_KEY=sk-ant-... # If you have Anthropic

# Optional: Add more providers
GOOGLE_API_KEY=...
MISTRAL_API_KEY=...
```

## Step 3: Start Synapse

```bash
# Start all services
make docker-up

# Check logs
make docker-logs
```

Synapse is now running at `http://localhost:8000` 🎉

## Step 4: Configure Your IDE

### For Cursor

1. Open Cursor Settings (⌘+,)
2. Go to **Models** → **Add Model**
3. Configure:
   - Model ID: `synapse`
   - API Base: `http://localhost:8000/v1`
   - API Key: `your-api-key` (from .env)

### For Cline (VSCode)

Add to settings.json:
```json
{
  "cline.apiProvider": "openai",
  "cline.apiUrl": "http://localhost:8000/v1",
  "cline.apiKey": "your-api-key",
  "cline.model": "synapse"
}
```

### For Continue

Edit `~/.continue/config.json`:
```json
{
  "models": [{
    "title": "Synapse",
    "provider": "openai",
    "model": "synapse",
    "apiKey": "your-api-key",
    "apiBase": "http://localhost:8000/v1"
  }]
}
```

## Step 5: Test It Out

```bash
# Test the API
curl http://localhost:8000/health

# Test chat completion
curl http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your-api-key" \\
  -d '{
    "model": "synapse",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 📚 Next Steps

1. **Index Your Documentation**
   ```bash
   # Upload your docs
   curl -X POST http://localhost:8000/api/documents/upload \\
     -H "Authorization: Bearer your-api-key" \\
     -F "files=@docs/README.md"
   ```

2. **Enable Memory**
   - Synapse automatically remembers conversations
   - Use `X-User-ID` header for user-specific memory

3. **Add Custom Tools**
   - Check `examples/mcp_tools.py` for MCP examples

## 🛟 Troubleshooting

### "Connection refused"
- Check if services are running: `docker ps`
- Check logs: `make docker-logs`

### "Invalid API key"
- Make sure your .env file has valid API keys
- Restart services: `make docker-down && make docker-up`

### "Out of memory"
- Synapse needs ~2GB RAM minimum
- Reduce vector dimensions in config if needed

## 🤝 Need Help?

- 📖 [Full Documentation](https://github.com/eagurin/synapse/wiki)
- 💬 [Discord Community](https://discord.gg/synapse)
- 🐛 [Report Issues](https://github.com/eagurin/synapse/issues)""",

    "LICENSE": """MIT License

Copyright (c) 2024 Synapse Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""",

    "CONTRIBUTING.md": """# Contributing to Synapse

Thank you for your interest in contributing to Synapse! 

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/synapse.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Make your changes
5. Run tests: `make test`
6. Commit: `git commit -m 'Add amazing feature'`
7. Push: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
make format

# Run linter
make lint
```

## Code Style

- Use Black for formatting
- Follow PEP 8
- Add type hints where possible
- Write docstrings for all functions

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage

## Pull Request Process

1. Update README.md with details of changes if needed
2. Update the docs with any new functionality
3. The PR will be merged once you have approval

## Questions?

Feel free to open an issue or join our Discord!""",

    "pyproject.toml": """[tool.poetry]
name = "synapse"
version = "0.1.0"
description = "Self-hosted AI backend for Cursor/Cline/Continue with persistent memory"
authors = ["Synapse Contributors"]
license = "MIT"
readme = "README.md"
homepage = "https://github.com/eagurin/synapse"
repository = "https://github.com/eagurin/synapse"
keywords = ["ai", "llm", "openai", "cursor", "cline", "memory", "rag"]

[tool.poetry.dependencies]
python = "^3.10"

[tool.black]
line-length = 88
target-version = ['py310', 'py311']
include = '\\.pyi?$'

[tool.ruff]
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long
    "B008",  # do not perform function calls in argument defaults
    "W191",  # indentation contains tabs
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api" """,
}

# Python files with proper module structure
PYTHON_FILES = {
    "app/__init__.py": '''"""
Synapse - Self-hosted AI backend for Cursor/Cline/Continue
"""

__version__ = "0.1.0"
__author__ = "Synapse Contributors"
__license__ = "MIT"''',

    "app/main.py": '''"""
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
    )''',

    "app/api/__init__.py": '''"""API endpoints"""
from app.api import chat, health, memory, documents

__all__ = ["chat", "health", "memory", "documents"]''',

    "app/api/health.py": '''"""Health check endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "synapse",
        "version": "0.1.0"
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check - verifies all services are ready"""
    try:
        # Check database
        await db.execute(text("SELECT 1"))
        
        # TODO: Check Redis
        # TODO: Check R2R
        # TODO: Check Mem0
        
        return {
            "status": "ready",
            "services": {
                "database": "healthy",
                "redis": "healthy",
                "r2r": "healthy",
                "mem0": "healthy"
            }
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e)
        }''',

    "app/api/chat.py": '''"""OpenAI-compatible chat completions endpoint"""
import time
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "synapse"
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    user: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    req: Request,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """OpenAI-compatible chat completions endpoint"""
    
    # Get user ID from header or request
    user_id = x_user_id or request.user or "default"
    
    # Get services from app state
    services = req.app.state.services
    
    try:
        if request.stream:
            # Streaming response
            return StreamingResponse(
                stream_chat_completion(request, services, user_id),
                media_type="text/event-stream"
            )
        else:
            # Regular response
            response = await generate_chat_completion(request, services, user_id)
            return response
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def generate_chat_completion(
    request: ChatCompletionRequest,
    services,
    user_id: str
) -> ChatCompletionResponse:
    """Generate a chat completion"""
    
    # TODO: Implement actual logic with LiteLLM + Mem0 + R2R
    # For now, return a mock response
    
    completion_id = f"chatcmpl-{uuid.uuid4()}"
    
    return ChatCompletionResponse(
        id=completion_id,
        created=int(time.time()),
        model=request.model,
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! I'm Synapse, your AI assistant with persistent memory. This is a placeholder response - the actual implementation will integrate LiteLLM, Mem0, and R2R."
            },
            "finish_reason": "stop"
        }],
        usage={
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    )


async def stream_chat_completion(request, services, user_id):
    """Stream a chat completion"""
    
    # TODO: Implement actual streaming with LiteLLM
    # For now, yield mock SSE events
    
    completion_id = f"chatcmpl-{uuid.uuid4()}"
    
    # Initial chunk
    yield f"data: {{"
    yield f'"id":"{completion_id}",'
    yield f'"object":"chat.completion.chunk",'
    yield f'"created":{int(time.time())},'
    yield f'"model":"{request.model}",'
    yield f'"choices":[{{"index":0,"delta":{{"role":"assistant"}},"finish_reason":null}}]'
    yield f"}}\\n\\n"
    
    # Content chunks
    content = "Hello! I'm Synapse. This is a streaming response placeholder."
    for word in content.split():
        yield f"data: {{"
        yield f'"id":"{completion_id}",'
        yield f'"object":"chat.completion.chunk",'
        yield f'"created":{int(time.time())},'
        yield f'"model":"{request.model}",'
        yield f'"choices":[{{"index":0,"delta":{{"content":" {word}"}},"finish_reason":null}}]'
        yield f"}}\\n\\n"
    
    # Final chunk
    yield f"data: {{"
    yield f'"id":"{completion_id}",'
    yield f'"object":"chat.completion.chunk",'
    yield f'"created":{int(time.time())},'
    yield f'"model":"{request.model}",'
    yield f'"choices":[{{"index":0,"delta":{{}},"finish_reason":"stop"}}]'
    yield f"}}\\n\\n"
    
    yield "data: [DONE]\\n\\n"


@router.get("/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            {
                "id": "synapse",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "synapse",
                "permission": [],
                "root": "synapse",
                "parent": None,
            },
            {
                "id": "synapse-fast",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "synapse",
            },
            {
                "id": "synapse-smart",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "synapse",
            }
        ]
    }''',

    "app/api/memory.py": '''"""Memory management endpoints"""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router = APIRouter()


class MemoryCreate(BaseModel):
    content: str
    type: str = "general"
    metadata: Optional[dict] = None


@router.get("/memory/{user_id}")
async def get_user_memory(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get all memories for a user"""
    # TODO: Implement with Mem0
    return {
        "user_id": user_id,
        "memories": [],
        "count": 0
    }


@router.post("/memory/{user_id}")
async def create_memory(
    user_id: str,
    memory: MemoryCreate,
    authorization: Optional[str] = Header(None)
):
    """Create a new memory for a user"""
    # TODO: Implement with Mem0
    return {
        "status": "created",
        "user_id": user_id,
        "memory_id": "placeholder"
    }


@router.delete("/memory/{user_id}/{memory_id}")
async def delete_memory(
    user_id: str,
    memory_id: str,
    authorization: Optional[str] = Header(None)
):
    """Delete a specific memory"""
    # TODO: Implement with Mem0
    return {
        "status": "deleted",
        "memory_id": memory_id
    }''',

    "app/api/documents.py": '''"""Document management endpoints"""
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from pydantic import BaseModel

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    use_memory: bool = True


@router.post("/documents/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    authorization: Optional[str] = Header(None)
):
    """Upload documents to the RAG system"""
    # TODO: Implement with R2R
    uploaded = []
    
    for file in files:
        # TODO: Process and index file
        uploaded.append({
            "filename": file.filename,
            "size": file.size,
            "status": "indexed"
        })
    
    return {
        "status": "success",
        "documents": uploaded,
        "count": len(uploaded)
    }


@router.post("/documents/search")
async def search_documents(
    request: SearchRequest,
    x_user_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    """Search documents with optional memory context"""
    # TODO: Implement with R2R + Mem0
    return {
        "query": request.query,
        "results": [],
        "count": 0,
        "user_context_applied": request.use_memory and x_user_id is not None
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    authorization: Optional[str] = Header(None)
):
    """Delete a document from the system"""
    # TODO: Implement with R2R
    return {
        "status": "deleted",
        "document_id": document_id
    }''',

    "app/core/__init__.py": '''"""Core functionality"""''',

    "app/core/config.py": '''"""Application configuration"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # API
    API_KEY: str = "default-api-key"
    JWT_SECRET: str = "default-jwt-secret"
    
    # Database
    DATABASE_URL: str = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    REPLICATE_API_TOKEN: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    
    # Local models
    OLLAMA_HOST: Optional[str] = "http://localhost:11434"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Optional services
    SENTRY_DSN: Optional[str] = None
    ENABLE_PROMETHEUS: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Validate critical settings
if settings.ENVIRONMENT == "production":
    if settings.API_KEY == "default-api-key":
        raise ValueError("API_KEY must be set in production")
    if settings.JWT_SECRET == "default-jwt-secret":
        raise ValueError("JWT_SECRET must be set in production")''',

    "app/core/database.py": '''"""Database configuration and session management"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.ENVIRONMENT == "development",
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database"""
    # Create schemas
    async with engine.begin() as conn:
        await conn.execute("CREATE SCHEMA IF NOT EXISTS r2r")
        await conn.execute("CREATE SCHEMA IF NOT EXISTS mem0")
        await conn.execute("CREATE SCHEMA IF NOT EXISTS shared")
        
        # TODO: Run alembic migrations
        # For now, just ensure extensions
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')''',

    "app/core/services.py": '''"""Service manager for initializing all services"""
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages all application services"""
    
    def __init__(self):
        self.llm = None
        self.memory = None
        self.rag = None
        self.mcp = None
        
    async def initialize(self):
        """Initialize all services"""
        logger.info("Initializing services...")
        
        # Initialize LLM service
        await self._init_llm()
        
        # Initialize Memory service
        await self._init_memory()
        
        # Initialize RAG service
        await self._init_rag()
        
        # Initialize MCP service
        await self._init_mcp()
        
        logger.info("✅ All services initialized")
    
    async def _init_llm(self):
        """Initialize LiteLLM with available providers"""
        try:
            # TODO: Import and initialize actual LiteLLM service
            logger.info("Initializing LLM service...")
            
            # Check available providers
            providers = []
            if settings.OPENAI_API_KEY:
                providers.append("openai")
            if settings.ANTHROPIC_API_KEY:
                providers.append("anthropic")
            if settings.GOOGLE_API_KEY:
                providers.append("google")
            
            logger.info(f"Available LLM providers: {providers}")
            
            # self.llm = LLMService(providers)
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    async def _init_memory(self):
        """Initialize Mem0 memory system"""
        try:
            logger.info("Initializing Memory service...")
            
            # TODO: Import and initialize actual Mem0
            # self.memory = MemoryService(settings.DATABASE_URL)
            
        except Exception as e:
            logger.error(f"Failed to initialize Memory service: {e}")
            raise
    
    async def _init_rag(self):
        """Initialize R2R RAG system"""
        try:
            logger.info("Initializing RAG service...")
            
            # TODO: Import and initialize actual R2R
            # self.rag = RAGService(settings.DATABASE_URL)
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    async def _init_mcp(self):
        """Initialize MCP servers"""
        try:
            logger.info("Initializing MCP service...")
            
            # TODO: Import and initialize FastMCP
            # self.mcp = MCPService()
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP service: {e}")
            raise
    
    async def shutdown(self):
        """Cleanup services on shutdown"""
        logger.info("Shutting down services...")
        
        # TODO: Implement cleanup for each service
        
        logger.info("✅ All services shut down")''',

    "app/services/__init__.py": '''"""Service implementations"""''',

    "app/models/__init__.py": '''"""Database models and schemas"""''',

    "tests/__init__.py": '''"""Test suite for Synapse"""''',

    "tests/test_api.py": '''"""Basic API tests"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Synapse"


def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_completions():
    """Test chat completions endpoint"""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "synapse",
            "messages": [{"role": "user", "content": "Hello"}]
        },
        headers={"Authorization": "Bearer test-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0


def test_list_models():
    """Test models endpoint"""
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0''',

    "scripts/init.sql": '''-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS r2r;
CREATE SCHEMA IF NOT EXISTS mem0;
CREATE SCHEMA IF NOT EXISTS shared;

-- Grant permissions
GRANT ALL ON SCHEMA r2r TO synapse;
GRANT ALL ON SCHEMA mem0 TO synapse;
GRANT ALL ON SCHEMA shared TO synapse;

-- Shared entities table (knowledge graph)
CREATE TABLE IF NOT EXISTS shared.entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    source_system TEXT CHECK (source_system IN ('r2r', 'mem0', 'both'))
);

-- Shared relationships table
CREATE TABLE IF NOT EXISTS shared.relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_entity_id UUID REFERENCES shared.entities(id) ON DELETE CASCADE,
    to_entity_id UUID REFERENCES shared.entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    properties JSONB DEFAULT '{}',
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    source_system TEXT CHECK (source_system IN ('r2r', 'mem0', 'both'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_entities_embedding ON shared.entities 
    USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_entities_name ON shared.entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON shared.entities(type);
CREATE INDEX IF NOT EXISTS idx_relationships_from_to ON shared.relationships(from_entity_id, to_entity_id);''',

    ".github/workflows/ci.yml": '''name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: ankane/pgvector:v0.5.1
        env:
          POSTGRES_USER: synapse
          POSTGRES_PASSWORD: synapse_password
          POSTGRES_DB: synapse_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run linter
      run: |
        ruff check app/ tests/
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://synapse:synapse_password@localhost:5432/synapse_db
        REDIS_URL: redis://localhost:6379
      run: |
        pytest tests/ -v --tb=short
    
    - name: Check code formatting
      run: |
        black --check app/ tests/

  docker:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t synapse:test .
    
    - name: Test Docker image
      run: |
        docker run --rm synapse:test python -c "import app; print('✅ Import successful')"''',
}

# Example files
EXAMPLE_FILES = {
    "examples/basic_chat.py": '''"""Basic chat example using Synapse API"""
import os
from openai import OpenAI

# Configure client to use Synapse
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key=os.getenv("API_KEY", "your-api-key")
)

# Simple chat
response = client.chat.completions.create(
    model="synapse",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Synapse?"}
    ]
)

print("Response:", response.choices[0].message.content)

# Streaming example
print("\\nStreaming response:")
stream = client.chat.completions.create(
    model="synapse",
    messages=[
        {"role": "user", "content": "Tell me a short story"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
print()

# With user context (for memory)
response = client.chat.completions.create(
    model="synapse",
    messages=[
        {"role": "user", "content": "Remember that my favorite color is blue"}
    ],
    user="user123"  # This enables user-specific memory
)

print("\\nMemory stored:", response.choices[0].message.content)''',

    "examples/upload_docs.py": '''"""Example: Upload documents to Synapse"""
import os
import requests
from pathlib import Path

# Configuration
SYNAPSE_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "your-api-key")

# Headers
headers = {
    "Authorization": f"Bearer {API_KEY}"
}


def upload_file(filepath: str):
    """Upload a single file"""
    with open(filepath, 'rb') as f:
        files = {'files': (Path(filepath).name, f)}
        response = requests.post(
            f"{SYNAPSE_URL}/api/documents/upload",
            headers=headers,
            files=files
        )
    
    if response.status_code == 200:
        print(f"✅ Uploaded: {filepath}")
    else:
        print(f"❌ Failed to upload {filepath}: {response.text}")
    
    return response.json()


def upload_directory(directory: str):
    """Upload all documents from a directory"""
    path = Path(directory)
    files_to_upload = []
    
    # Supported extensions
    extensions = {'.txt', '.md', '.pdf', '.docx', '.html', '.json', '.py', '.js', '.ts'}
    
    for file in path.rglob('*'):
        if file.is_file() and file.suffix.lower() in extensions:
            files_to_upload.append(str(file))
    
    print(f"Found {len(files_to_upload)} files to upload")
    
    for filepath in files_to_upload:
        upload_file(filepath)


def search_documents(query: str, use_memory: bool = True):
    """Search uploaded documents"""
    response = requests.post(
        f"{SYNAPSE_URL}/api/documents/search",
        headers=headers,
        json={
            "query": query,
            "limit": 5,
            "use_memory": use_memory
        }
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"\\nSearch results for '{query}':")
        print(f"Found {results['count']} results")
        
        for i, result in enumerate(results.get('results', [])):
            print(f"\\n{i+1}. {result.get('title', 'Untitled')}")
            print(f"   Score: {result.get('score', 0):.3f}")
            print(f"   Preview: {result.get('preview', '')[:100]}...")
    else:
        print(f"Search failed: {response.text}")


if __name__ == "__main__":
    # Example 1: Upload a single file
    # upload_file("docs/README.md")
    
    # Example 2: Upload entire directory
    # upload_directory("docs/")
    
    # Example 3: Search documents
    # search_documents("How to deploy Synapse?")
    
    print("Update this script with your file paths and run!")''',

    "examples/mcp_tools.py": '''"""Example: Creating custom MCP tools for Synapse"""
from fastmcp import FastMCP
import httpx
import subprocess
from datetime import datetime

# Create MCP server
mcp = FastMCP("synapse-tools")


@mcp.tool()
async def web_search(query: str) -> str:
    """Search the web for information"""
    # Example using DuckDuckGo (no API key needed)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1}
        )
        
        if response.status_code == 200:
            data = response.json()
            abstract = data.get("AbstractText", "")
            if abstract:
                return f"Summary: {abstract}"
            else:
                return "No summary found. Try a more specific query."
        else:
            return f"Search failed with status {response.status_code}"


@mcp.tool()
async def run_sql_query(query: str, database: str = "main") -> dict:
    """Execute a read-only SQL query
    
    Args:
        query: SQL query to execute (SELECT only)
        database: Database name (default: main)
    
    Returns:
        Query results as dict
    """
    # Validate query is read-only
    if not query.strip().upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed"}
    
    # TODO: Implement actual database connection
    # This is just an example structure
    return {
        "columns": ["id", "name", "created_at"],
        "rows": [
            [1, "Example", "2024-01-01"],
            [2, "Demo", "2024-01-02"]
        ],
        "row_count": 2
    }


@mcp.tool()
async def get_system_info() -> dict:
    """Get current system information"""
    import platform
    import psutil
    
    return {
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total": psutil.virtual_memory().total // (1024**3),  # GB
            "available": psutil.virtual_memory().available // (1024**3),
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": psutil.disk_usage('/').total // (1024**3),
            "free": psutil.disk_usage('/').free // (1024**3),
            "percent": psutil.disk_usage('/').percent
        }
    }


@mcp.tool()
async def execute_code(code: str, language: str = "python") -> str:
    """Execute code in a sandboxed environment
    
    Args:
        code: Code to execute
        language: Programming language (python, javascript, bash)
    
    Returns:
        Output from code execution
    """
    # WARNING: This is just an example. In production, use proper sandboxing!
    
    if language == "python":
        try:
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.flush()
                
                # Execute with timeout
                result = subprocess.run(
                    ["python", f.name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                return f"Output:\\n{result.stdout}\\n\\nErrors:\\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Code execution timed out (5 second limit)"
        except Exception as e:
            return f"Execution failed: {str(e)}"
    
    else:
        return f"Language '{language}' not supported. Use: python"


@mcp.tool()
async def create_reminder(
    message: str, 
    time: str,
    user_id: str = "default"
) -> dict:
    """Create a reminder for the user
    
    Args:
        message: Reminder message
        time: When to remind (e.g., "in 5 minutes", "tomorrow at 9am")
        user_id: User ID for the reminder
    
    Returns:
        Confirmation of reminder creation
    """
    # TODO: Implement actual reminder system
    # This would integrate with your notification system
    
    return {
        "status": "created",
        "reminder": {
            "message": message,
            "time": time,
            "user_id": user_id,
            "id": "reminder_123"
        }
    }


# To integrate with Synapse:
# 1. Save this file
# 2. Register the MCP server with Synapse
# 3. The tools will be available to the AI

if __name__ == "__main__":
    # Test the tools locally
    import asyncio
    
    async def test():
        result = await web_search("Python FastAPI")
        print("Search result:", result)
        
        info = await get_system_info()
        print("\\nSystem info:", info)
    
    asyncio.run(test())''',
}


def create_file(path: Path, content: str):
    """Create a file with content"""
    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write content
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created: {path}")


def main():
    """Create all project files"""
    print("🚀 Creating Synapse project files...")
    print("=" * 50)
    
    # Create root files
    for filename, content in FILES.items():
        create_file(Path(filename), content)
    
    # Create Python files
    for filename, content in PYTHON_FILES.items():
        create_file(Path(filename), content)
    
    # Create example files
    for filename, content in EXAMPLE_FILES.items():
        create_file(Path(filename), content)
    
    # Create empty __init__.py files if they don't exist
    init_files = [
        "app/__init__.py",
        "app/api/__init__.py", 
        "app/core/__init__.py",
        "app/services/__init__.py",
        "app/models/__init__.py",
        "tests/__init__.py"
    ]
    
    for init_file in init_files:
        path = Path(init_file)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            print(f"✅ Created: {init_file}")
    
    # Copy .env.example to .env if it doesn't exist
    if not Path(".env").exists() and Path(".env.example").exists():
        import shutil
        shutil.copy(".env.example", ".env")
        print("✅ Created .env from .env.example")
    
    print("=" * 50)
    print("✨ All files created successfully!")
    print("\nNext steps:")
    print("1. Edit .env with your API keys")
    print("2. Run 'make docker-up' to start services")
    print("3. Visit http://localhost:8000")
    print("\nTo commit everything:")
    print("git add .")
    print('git commit -m "Initial commit: Synapse AI backend"')
    print("git push origin main")


if __name__ == "__main__":
    main()
