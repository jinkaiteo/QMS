# QMS System Endpoints
# Phase 1: System management and health endpoints

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db, db_manager
from app.core.config import settings
from app.models.system import SystemSetting

router = APIRouter()


@router.get("/health")
async def health_check():
    """Comprehensive system health check"""

    # Database health check
    db_health = db_manager.health_check()

    # Application health
    health_status = {
        "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {"database": db_health, "application": {"status": "healthy", "version": settings.APP_VERSION}},
    }

    return health_status


@router.get("/info")
async def system_info():
    """Get system information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "compliance": "21 CFR Part 11",
        "features": [
            "Electronic Document Management",
            "Quality Record Management",
            "Training Record Management",
            "Laboratory Information Management",
            "Digital Signatures",
            "Audit Trail",
        ],
    }


@router.get("/settings")
async def get_system_settings(db: Session = Depends(get_db)):
    """Get public system settings"""
    settings = db.query(SystemSetting).filter(
        SystemSetting.is_system == False,
        SystemSetting.is_encrypted == False
    ).all()
    
    return {setting.key: setting.value for setting in settings}


@router.get("/database/status")
async def database_status():
    """Get database connection status and statistics"""
    return db_manager.get_connection_info()
