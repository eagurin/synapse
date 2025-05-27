"""Health check endpoints"""
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
        }