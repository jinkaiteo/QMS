# QMS Backend Configuration
# Phase 1: Application settings and environment configuration

from typing import List, Optional, Any, Dict
from pydantic import AnyHttpUrl, validator, PostgresDsn
from pydantic_settings import BaseSettings
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "QMS Pharmaceutical System"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        # Build PostgreSQL URL manually for Pydantic v2 compatibility
        user = values.get("POSTGRES_USER", "")
        password = values.get("POSTGRES_PASSWORD", "")
        host = values.get("POSTGRES_SERVER", "localhost")
        port = values.get("POSTGRES_PORT", "5432")
        db = values.get("POSTGRES_DB", "")
        
        if user and password:
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"
        else:
            return f"postgresql://{host}:{port}/{db}"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Trusted hosts for production
    ALLOWED_HOSTS: List[str] = [
        "localhost", 
        "127.0.0.1", 
        "qms-platform.local",
        "localhost:8443",
        "127.0.0.1:8443",
        "qms-platform.local:8443",
        "qms-app-prod",
        "qms-app-prod:8000"
    ]
    
    # File Storage
    UPLOAD_PATH: str = "/app/uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [
        "pdf", "docx", "doc", "xlsx", "xls", 
        "pptx", "ppt", "txt", "png", "jpg", "jpeg"
    ]
    
    # MinIO/S3 Configuration
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_NAME: str = "qms-documents"
    
    # Document storage settings (Phase 2)
    DOCUMENT_STORAGE_PATH: str = "/app/storage/documents"
    MAX_DOCUMENT_SIZE_MB: int = 100
    ALLOWED_DOCUMENT_EXTENSIONS: list = [
        ".pdf", ".docx", ".doc", ".xlsx", ".xls", 
        ".pptx", ".ppt", ".txt", ".rtf"
    ]
    MINIO_SECURE: bool = False
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    
    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Microsoft Entra ID (Azure AD)
    AZURE_AD_TENANT_ID: Optional[str] = None
    AZURE_AD_CLIENT_ID: Optional[str] = None
    AZURE_AD_CLIENT_SECRET: Optional[str] = None
    
    # Compliance Settings
    CFR_21_PART_11_ENABLED: bool = True
    AUDIT_LOG_RETENTION_YEARS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_COMPLEXITY_REQUIRED: bool = True
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30
    SESSION_TIMEOUT_MINUTES: int = 480  # 8 hours
    
    # Digital Signatures
    SIGNATURE_CERT_PATH: Optional[str] = None
    SIGNATURE_KEY_PATH: Optional[str] = None
    SIGNATURE_KEY_PASSWORD: Optional[str] = None
    TIMESTAMP_AUTHORITY_URL: str = "http://timestamp.digicert.com"
    
    # Monitoring
    ENABLE_METRICS: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    # Backup Configuration
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM
    BACKUP_RETENTION_DAYS: int = 90
    BACKUP_PATH: str = "/app/backups"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Development settings
class DevelopmentSettings(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENVIRONMENT: str = "development"
    
    # Default development database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "qms_user"
    POSTGRES_PASSWORD: str = "qms_dev_password"
    POSTGRES_DB: str = "qms_dev"
    
    # Development security (less strict)
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours for development
    
    # Development CORS (allow all origins)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Current frontend dev server
        "http://127.0.0.1:3001",
        "http://localhost:3002",  # Backup frontend port
        "http://127.0.0.1:3002",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]


# Production settings
class ProductionSettings(Settings):
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"
    
    # Production security
    PASSWORD_COMPLEXITY_REQUIRED: bool = True
    RATE_LIMIT_ENABLED: bool = True
    CFR_21_PART_11_ENABLED: bool = True
    
    # Stricter session timeout
    SESSION_TIMEOUT_MINUTES: int = 240  # 4 hours


# Testing settings
class TestingSettings(Settings):
    DEBUG: bool = True
    ENVIRONMENT: str = "testing"
    
    # Test database
    POSTGRES_DB: str = "qms_test"
    
    # Fast tokens for testing
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    
    # Disable external services for testing
    BACKUP_ENABLED: bool = False
    ENABLE_METRICS: bool = False


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()


# Ensure upload directory exists
def ensure_directories():
    """Ensure required directories exist"""
    # Skip directory creation in testing environment or when permissions are insufficient
    if os.getenv("ENVIRONMENT") == "testing":
        return
        
    directories = [
        settings.UPLOAD_PATH,
        settings.BACKUP_PATH,
        "/app/logs",
        "/app/temp"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            # Skip directory creation if permissions are insufficient or in CI environment
            pass


# Call on import
ensure_directories()
