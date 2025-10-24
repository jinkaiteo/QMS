# QMS User Schemas
# Phase 1: Pydantic schemas for user management

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator

from app.models.user import UserStatus


class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    employee_id: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    password: str
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_id: Optional[str] = None
    phone: Optional[str] = None
    organization_id: Optional[int] = None
    department_id: Optional[int] = None


class UserResponse(UserBase):
    """User response schema"""
    id: int
    uuid: str
    status: UserStatus
    organization_id: Optional[int]
    department_id: Optional[int]
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Base role schema"""
    name: str
    display_name: str
    description: Optional[str] = None
    module: str
    permissions: List[str]


class RoleResponse(RoleBase):
    """Role response schema"""
    id: int
    uuid: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str
    code: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class OrganizationResponse(OrganizationBase):
    """Organization response schema"""
    id: int
    uuid: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
