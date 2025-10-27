# QMS User Profile Schemas - Phase A Sprint 1
# Pydantic schemas for user profile management

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class UserPreferenceSchema(BaseModel):
    """User preference schema"""
    preference_key: str
    preference_value: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserSessionSchema(BaseModel):
    """User session schema"""
    id: int
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    started_at: datetime
    last_activity_at: datetime
    ended_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class UserProfileBase(BaseModel):
    """Base user profile schema"""
    phone_number: Optional[str] = None
    job_title: Optional[str] = None
    hire_date: Optional[date] = None
    employee_id: Optional[str] = None
    supervisor_id: Optional[int] = None
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        if v and len(v) < 3:
            raise ValueError('Employee ID must be at least 3 characters')
        return v


class UserProfileCreate(UserProfileBase):
    """Schema for creating user profile"""
    pass


class UserProfileUpdate(UserProfileBase):
    """Schema for updating user profile"""
    profile_picture_url: Optional[str] = None


class UserProfileResponse(UserProfileBase):
    """Schema for user profile response"""
    id: int
    username: str
    email: EmailStr
    full_name: str
    profile_picture_url: Optional[str] = None
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Related data
    preferences: List[UserPreferenceSchema] = []
    supervisor: Optional['UserSummarySchema'] = None
    
    class Config:
        from_attributes = True


class UserSummarySchema(BaseModel):
    """Summary schema for user references"""
    id: int
    username: str
    full_name: str
    job_title: Optional[str] = None
    profile_picture_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserActivitySummary(BaseModel):
    """User activity summary schema"""
    user_id: int
    period_days: int
    total_sessions: int
    total_active_time_minutes: int
    login_frequency: float
    last_login: Optional[datetime] = None
    most_active_hour: Optional[int] = None
    device_types: Dict[str, int] = {}


class BulkUserUpdate(BaseModel):
    """Schema for bulk user updates"""
    user_ids: List[int]
    updates: Dict[str, Any]
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one user ID is required')
        if len(v) > 100:
            raise ValueError('Maximum 100 users can be updated at once')
        return v


class PasswordPolicySchema(BaseModel):
    """Password policy configuration schema"""
    min_length: int = 8
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    require_non_dictionary: bool = False
    max_age_days: Optional[int] = 90
    remember_last_passwords: int = 5
    lockout_attempts: int = 5
    lockout_duration_minutes: int = 30
    
    @validator('min_length')
    def validate_min_length(cls, v):
        if v < 6:
            raise ValueError('Minimum password length cannot be less than 6')
        return v


class UserOnboardingRequest(BaseModel):
    """Schema for user onboarding request"""
    username: str
    email: EmailStr
    full_name: str
    job_title: Optional[str] = None
    department_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    employee_id: Optional[str] = None
    role_ids: List[int] = []
    send_welcome_email: bool = True
    require_password_change: bool = True
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.replace('_', '').replace('.', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, dots, and underscores')
        return v.lower()


class UserOnboardingResponse(BaseModel):
    """Schema for user onboarding response"""
    user_id: int
    username: str
    email: EmailStr
    temporary_password: Optional[str] = None  # Only returned if not using email
    onboarding_token: str
    welcome_email_sent: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Forward reference resolution
UserProfileResponse.model_rebuild()