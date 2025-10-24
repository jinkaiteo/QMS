# QMS Authentication Schemas
# Phase 1: Pydantic schemas for authentication

from typing import List, Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str
    mfa_code: Optional[str] = None


class UserInfo(BaseModel):
    """User information in token response"""
    id: int
    username: str
    email: EmailStr
    full_name: str
    roles: List[str]
    permissions: List[str]


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserInfo


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str
