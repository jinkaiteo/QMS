# QMS API v1 Router
# Phase 1: Main API router configuration

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, system, documents, quality_events, capas, training, lims

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
# Phase 2: EDMS endpoints
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
# Phase 3: QRM endpoints
api_router.include_router(quality_events.router, prefix="/quality-events", tags=["quality-events"])
api_router.include_router(capas.router, prefix="/capas", tags=["capas"])
api_router.include_router(training.router, prefix="/training", tags=["training"])
api_router.include_router(lims.router, prefix="/lims", tags=["lims"])
