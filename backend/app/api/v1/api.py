# QMS API v1 Router
# Phase 1: Main API router configuration

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, system, training_simple
# Temporarily disabled problematic modules: documents, quality_events, capas, lims, user_profiles, business_calendar, predictive_scheduling, advanced_analytics, compliance_automation, notification_system, document_upload, document_workflow, document_version
# department_hierarchy temporarily disabled due to model conflicts

api_router = APIRouter()

# Include endpoint routers - Core functionality only
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(training_simple.router, prefix="/training", tags=["training"])

# Temporarily disabled all other endpoints due to Pydantic v2 compatibility issues
# api_router.include_router(user_profiles.router, prefix="/user-profiles", tags=["user-profiles"])
# api_router.include_router(department_hierarchy.router, prefix="/org", tags=["organization"])
# api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
# api_router.include_router(quality_events.router, prefix="/quality-events", tags=["quality-events"])
# api_router.include_router(capas.router, prefix="/capas", tags=["capas"])
# api_router.include_router(document_upload.router, prefix="/documents", tags=["document-upload"])
# api_router.include_router(document_workflow.router, prefix="/workflow", tags=["document-workflow"])
# api_router.include_router(document_version.router, prefix="/versions", tags=["document-version"])
# api_router.include_router(lims.router, prefix="/lims", tags=["lims"])
# api_router.include_router(business_calendar.router, prefix="/business-calendar", tags=["business-calendar"])
# api_router.include_router(predictive_scheduling.router, prefix="/predictive-scheduling", tags=["predictive-scheduling"])
# api_router.include_router(advanced_analytics.router, prefix="/advanced-analytics", tags=["advanced-analytics"])
# api_router.include_router(compliance_automation.router, prefix="/compliance", tags=["compliance"])
# api_router.include_router(notification_system.router, prefix="/notifications", tags=["notifications"])
