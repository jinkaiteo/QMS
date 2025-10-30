# QMS System Models
# Phase 1: System configuration and settings models

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class SystemSetting(BaseModel):
    """System settings and configuration model"""
    
    __tablename__ = "system_settings"
    
    key = Column(String(255), unique=True, nullable=False, comment="Setting key identifier")
    value = Column(JSONB, comment="Setting value (can be any JSON type)")
    description = Column(Text, comment="Setting description")
    is_encrypted = Column(Boolean, default=False, comment="Whether the value is encrypted")
    category = Column(String(100), comment="Setting category for organization")
    is_system = Column(Boolean, default=False, comment="System setting (not user-modifiable)")
    
    # Change tracking
    updated_by = Column(Integer, ForeignKey("users.id"), comment="User who last updated the setting")
    
    # Relationships
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<SystemSetting(key={self.key})>"
    
    @classmethod
    def get_setting(cls, db_session, key: str, default=None):
        """Get a system setting value"""
        setting = db_session.query(cls).filter(cls.key == key).first()
        if setting:
            return setting.value
        return default
    
    @classmethod
    def set_setting(cls, db_session, key: str, value, description: str = None, user_id: int = None):
        """Set a system setting value"""
        setting = db_session.query(cls).filter(cls.key == key).first()
        
        if setting:
            setting.value = value
            setting.updated_by = user_id
            if description:
                setting.description = description
        else:
            setting = cls(
                key=key,
                value=value,
                description=description,
                updated_by=user_id
            )
            db_session.add(setting)
        
        db_session.commit()
        return setting


class ApplicationMetadata(BaseModel):
    """Application metadata and version information"""
    
    __tablename__ = "application_metadata"
    
    component = Column(String(100), nullable=False, comment="Application component name")
    version = Column(String(50), nullable=False, comment="Component version")
    build_number = Column(String(100), comment="Build number")
    build_date = Column(String(50), comment="Build date")
    git_commit = Column(String(100), comment="Git commit hash")
    environment = Column(String(50), comment="Deployment environment")
    
    # Metadata
    app_metadata = Column(JSONB, comment="Additional component metadata")
    
    def __repr__(self):
        return f"<ApplicationMetadata(component={self.component}, version={self.version})>"


class NotificationTemplate(BaseModel):
    """Email and notification templates"""
    
    __tablename__ = "notification_templates"
    
    name = Column(String(100), unique=True, nullable=False, comment="Template name")
    type = Column(String(50), nullable=False, comment="Notification type (email, sms, push)")
    subject_template = Column(String(255), comment="Subject line template")
    body_template = Column(Text, nullable=False, comment="Message body template")
    
    # Template Configuration
    variables = Column(JSONB, comment="Available template variables")
    is_html = Column(Boolean, default=False, comment="Whether body is HTML formatted")
    is_active = Column(Boolean, default=True, comment="Whether template is active")
    
    # Categorization
    category = Column(String(100), comment="Template category")
    module = Column(String(50), comment="QMS module this template belongs to")
    
    def __repr__(self):
        return f"<NotificationTemplate(name={self.name}, type={self.type})>"


class HealthCheck(BaseModel):
    """System health check results"""
    
    __tablename__ = "health_checks"
    
    check_name = Column(String(100), nullable=False, comment="Name of the health check")
    check_type = Column(String(50), nullable=False, comment="Type of check (database, redis, etc.)")
    status = Column(String(20), nullable=False, comment="Check status (healthy, unhealthy, warning)")
    
    # Check Results
    response_time_ms = Column(Integer, comment="Response time in milliseconds")
    details = Column(JSONB, comment="Detailed check results")
    error_message = Column(Text, comment="Error message if check failed")
    
    # Execution Info
    executed_at = Column(String(50), comment="Hostname where check was executed")
    
    def __repr__(self):
        return f"<HealthCheck(name={self.check_name}, status={self.status})>"
