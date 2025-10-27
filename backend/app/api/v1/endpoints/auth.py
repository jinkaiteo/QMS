# QMS Authentication Endpoints
# Phase 1: Basic authentication endpoints

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
import jwt

from app.core.database import get_db
from app.core.security import token_manager, security_utils, audit_logger
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo

router = APIRouter()
security = HTTPBearer()

# Simple in-memory token blacklist (in production, use Redis)
blacklisted_tokens = set()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers first (for proxy/load balancer scenarios)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct connection IP
    if hasattr(request.client, 'host'):
        return request.client.host
    
    return "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    return token in blacklisted_tokens


@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest, request: Request, db: Session = Depends(get_db)):
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
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
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
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
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
async def logout(request: Request, token: str = Depends(security)):
    """User logout endpoint with token blacklisting"""
    try:
        # Extract the actual token from the Bearer format
        auth_token = token.credentials
        
        # Decode token to get user info for audit logging
        try:
            payload = jwt.decode(
                auth_token, 
                token_manager.JWT_SECRET_KEY, 
                algorithms=[token_manager.ALGORITHM]
            )
            user_id = payload.get("sub")
            username = payload.get("username", "unknown")
        except jwt.InvalidTokenError:
            user_id = None
            username = "unknown"
        
        # Add token to blacklist
        blacklisted_tokens.add(auth_token)
        
        # Log logout event
        audit_logger.log_authentication_event(
            user_id=user_id,
            username=username,
            event_type="logout",
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return {"message": "Successfully logged out"}
    
    except Exception as e:
        # Log failed logout attempt
        audit_logger.log_authentication_event(
            user_id=None,
            username="unknown",
            event_type="logout",
            success=False,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        # Check if refresh token is blacklisted
        if is_token_blacklisted(refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Verify and decode refresh token
        try:
            payload = jwt.decode(
                refresh_token, 
                token_manager.JWT_SECRET_KEY, 
                algorithms=[token_manager.ALGORITHM]
            )
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if token_type != "refresh":
                raise jwt.InvalidTokenError("Not a refresh token")
                
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = token_manager.create_access_token(
            subject=user.id,
            additional_claims={
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name
            }
        )
        
        # Optionally create new refresh token (rotate refresh tokens)
        new_refresh_token = token_manager.create_refresh_token(subject=user.id)
        
        # Blacklist old refresh token
        blacklisted_tokens.add(refresh_token)
        
        # Log token refresh
        audit_logger.log_authentication_event(
            user_id=user.id,
            username=user.username,
            event_type="token_refresh",
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
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
        
    except HTTPException:
        raise
    except Exception as e:
        # Log failed refresh attempt
        audit_logger.log_authentication_event(
            user_id=None,
            username="unknown",
            event_type="token_refresh",
            success=False,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token refresh failed"
        )
