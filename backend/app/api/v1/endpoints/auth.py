# QMS Authentication Endpoints
# Phase 1: Basic authentication endpoints

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import token_manager, security_utils, audit_logger
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login endpoint
    Authenticates user and returns JWT tokens
    """
    # Find user by username
    user = db.query(User).filter(User.username == login_request.username).first()
    
    if not user or not security_utils.verify_password(login_request.password, user.password_hash):
        # Log failed login attempt
        audit_logger.log_authentication_event(
            user_id=user.id if user else None,
            username=login_request.username,
            event_type="login",
            success=False,
            ip_address="127.0.0.1",  # TODO: Get from request
            user_agent="FastAPI Test"  # TODO: Get from request
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Check if account is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is locked"
        )
    
    # Create tokens
    access_token = token_manager.create_access_token(
        subject=user.id,
        additional_claims={
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    )
    
    refresh_token = token_manager.create_refresh_token(subject=user.id)
    
    # Update user login info
    from datetime import datetime
    user.last_login = datetime.utcnow()
    user.login_count += 1
    user.failed_login_attempts = 0
    db.commit()
    
    # Log successful login
    audit_logger.log_authentication_event(
        user_id=user.id,
        username=user.username,
        event_type="login",
        success=True,
        ip_address="127.0.0.1",  # TODO: Get from request
        user_agent="FastAPI Test"  # TODO: Get from request
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes
        user=UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=[role.role.name for role in user.user_roles if role.is_active],
            permissions=user.get_permissions()
        )
    )


@router.post("/logout")
async def logout():
    """User logout endpoint"""
    # TODO: Implement token blacklisting
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    # TODO: Implement refresh token logic
    return {"message": "Token refreshed"}
