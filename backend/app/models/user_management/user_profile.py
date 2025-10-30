# QMS User Profile Models - Phase A Sprint 1
# SQLAlchemy models for enhanced user profile management

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET
from app.models.base import BaseModel


class UserPreference(BaseModel):
    """User preferences and settings model"""
    __tablename__ = "user_preferences"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'preference_key', name='uk_user_preferences_user_key'),
    )
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, key='{self.preference_key}')>"


class UserSession(BaseModel):
    """User login sessions for activity tracking"""
    __tablename__ = "user_sessions"
    __table_args__ = {'extend_existing': True}
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    ip_address = Column(INET)
    user_agent = Column(Text)
    started_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, token='{self.session_token[:8]}...', active={self.is_active})>"
    
    @property
    def session_duration(self):
        """Calculate session duration in seconds"""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        else:
            return (self.last_activity_at - self.started_at).total_seconds()
    
    @property
    def is_expired(self):
        """Check if session is expired (inactive for more than 24 hours)"""
        from datetime import datetime, timedelta
        if not self.is_active:
            return True
        
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        return self.last_activity_at < cutoff_time