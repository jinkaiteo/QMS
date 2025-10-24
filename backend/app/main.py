# QMS Backend Main Application
# Phase 1: FastAPI application setup with core services

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.core.security import SecurityMiddleware
from app.api.v1.api import api_router
from app.core.logging import setup_logging
from app.services.audit_service import AuditService


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("QMS Application starting up...")
    
    # Initialize database connection
    try:
        # Test database connection
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    # Initialize audit service
    app.state.audit_service = AuditService()
    logger.info("Audit service initialized")
    
    yield
    
    # Shutdown
    logger.info("QMS Application shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="21 CFR Part 11 Compliant Quality Management System",
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(SecurityMiddleware)

# CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Trusted host middleware for production
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header for performance monitoring"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def audit_requests(request: Request, call_next):
    """Audit HTTP requests for compliance"""
    # Skip audit for health checks and static files
    if request.url.path in ["/health", "/metrics"] or request.url.path.startswith("/static"):
        return await call_next(request)
    
    start_time = time.time()
    
    # Get client information
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    try:
        response = await call_next(request)
        
        # Log successful requests (except GET requests to reduce noise)
        if request.method != "GET" or response.status_code >= 400:
            # Try to get user ID from token if available
            user_id = getattr(request.state, "user_id", None)
            username = getattr(request.state, "username", "anonymous")
            
            # Log the request
            audit_data = {
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "response_time": time.time() - start_time,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user_id": user_id,
                "username": username
            }
            
            logger.info("HTTP Request", extra=audit_data)
        
        return response
        
    except Exception as e:
        # Log failed requests
        audit_data = {
            "method": request.method,
            "url": str(request.url),
            "error": str(e),
            "client_ip": client_ip,
            "user_agent": user_agent
        }
        
        logger.error("HTTP Request Failed", extra=audit_data)
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found"
            },
            "timestamp": time.time()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred"
            },
            "timestamp": time.time()
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    try:
        # Test database connection
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# Metrics endpoint for monitoring
@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic application information"""
    return {
        "message": "QMS Pharmaceutical System API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT != "production" else None,
        "compliance": "21 CFR Part 11"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
