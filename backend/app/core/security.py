# QMS Security Core
# Phase 1: Authentication, authorization, and security middleware

from datetime import datetime, timedelta
from typing import Any, Union, Optional, Dict, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import hashlib
import logging
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handler
security = HTTPBearer()


class SecurityUtils:
    """Security utility functions for 21 CFR Part 11 compliance"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash using direct bcrypt"""
        import bcrypt
        try:
            # Ensure password is bytes and within bcrypt limit
            password_bytes = plain_password.encode('utf-8')[:72]
            hash_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash using direct bcrypt"""
        import bcrypt
        try:
            # Ensure password is bytes and within bcrypt limit
            password_bytes = password.encode('utf-8')[:72]
            salt = bcrypt.gensalt()
            hash_bytes = bcrypt.hashpw(password_bytes, salt)
            return hash_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            # Fallback to simpler hash if bcrypt fails
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def validate_password_complexity(password: str) -> Dict[str, Any]:
        """
        Validate password complexity for pharmaceutical compliance
        Returns validation result with details
        """
        issues = []
        
        # Minimum length
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            issues.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        if settings.PASSWORD_COMPLEXITY_REQUIRED:
            # Check for uppercase
            if not any(c.isupper() for c in password):
                issues.append("Password must contain at least one uppercase letter")
            
            # Check for lowercase
            if not any(c.islower() for c in password):
                issues.append("Password must contain at least one lowercase letter")
            
            # Check for digits
            if not any(c.isdigit() for c in password):
                issues.append("Password must contain at least one number")
            
            # Check for special characters
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                issues.append("Password must contain at least one special character")
            
            # Check for common patterns
            if password.lower() in ['password', '123456', 'qwerty', 'admin']:
                issues.append("Password cannot be a common password")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def calculate_hash(data: str, algorithm: str = "sha256") -> str:
        """Calculate hash of data for integrity verification"""
        if algorithm == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(data.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")


class TokenManager:
    """JWT token management for authentication"""
    
    @staticmethod
    def create_access_token(
        subject: Union[str, Any], 
        expires_delta: timedelta = None,
        additional_claims: Dict = None
    ) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "type": "access",
            "iat": datetime.utcnow()
        }
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(subject: Union[str, Any]) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "type": "refresh",
            "iat": datetime.utcnow()
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                return None
            
            return payload
            
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    @staticmethod
    def extract_token_from_header(authorization: str) -> Optional[str]:
        """Extract token from Authorization header"""
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request processing"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security middleware"""
        
        # Add security headers to response
        response = await call_next(request)
        
        # Security headers for pharmaceutical compliance
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy for XSS protection (relaxed for API docs)
        if request.url.path.startswith("/api/v1/docs") or request.url.path.startswith("/api/v1/redoc"):
            # Relaxed CSP for Swagger UI
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
        else:
            # Strict CSP for production endpoints
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
        response.headers["Content-Security-Policy"] = csp
        
        return response


class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self):
        self.requests = {}  # In production, use Redis
    
    def is_allowed(self, identifier: str, limit: int = None) -> bool:
        """Check if request is allowed based on rate limit"""
        if not settings.RATE_LIMIT_ENABLED:
            return True
        
        if limit is None:
            limit = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        
        now = datetime.utcnow()
        minute_key = f"{identifier}:{now.strftime('%Y-%m-%d:%H:%M')}"
        
        current_count = self.requests.get(minute_key, 0)
        
        if current_count >= limit:
            return False
        
        self.requests[minute_key] = current_count + 1
        
        # Cleanup old entries (in production, use Redis with TTL)
        cleanup_time = now - timedelta(minutes=2)
        self.requests = {
            k: v for k, v in self.requests.items()
            if datetime.strptime(k.split(':', 1)[1], '%Y-%m-%d:%H:%M') > cleanup_time
        }
        
        return True


class AuditLogger:
    """Security audit logging for compliance"""
    
    @staticmethod
    def log_authentication_event(
        user_id: Optional[int],
        username: str,
        event_type: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        additional_info: Dict = None
    ):
        """Log authentication events for security audit"""
        audit_data = {
            "event_type": "authentication",
            "sub_type": event_type,
            "user_id": user_id,
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat(),
            "additional_info": additional_info or {}
        }
        
        if success:
            logger.info("Authentication event", extra=audit_data)
        else:
            logger.warning("Authentication failure", extra=audit_data)
    
    @staticmethod
    def log_authorization_event(
        user_id: int,
        username: str,
        resource: str,
        action: str,
        success: bool,
        ip_address: str
    ):
        """Log authorization events"""
        audit_data = {
            "event_type": "authorization",
            "user_id": user_id,
            "username": username,
            "resource": resource,
            "action": action,
            "success": success,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if success:
            logger.info("Authorization granted", extra=audit_data)
        else:
            logger.warning("Authorization denied", extra=audit_data)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current authenticated user from JWT token
    This function is used as a dependency in FastAPI endpoints
    """
    from app.core.database import get_db
    from app.models.user import User
    
    # Extract token
    token = credentials.credentials
    
    # Verify token
    payload = token_manager.verify_token(token, "access")
    if not payload:
        raise AuthenticationException("Invalid or expired token")
    
    # Extract user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Invalid token payload")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get user from database
        user = db.query(User).filter(
            User.id == int(user_id),
            User.is_deleted == False
        ).first()
        
        if not user:
            raise AuthenticationException("User not found")
        
        if user.status != "active":
            raise AuthenticationException("User account is not active")
        
        return user
        
    finally:
        db.close()


async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Get current active user (convenience function)
    """
    return current_user


# Global instances
security_utils = SecurityUtils()
token_manager = TokenManager()
rate_limiter = RateLimiter()
audit_logger = AuditLogger()


# Exception classes for security
class SecurityException(HTTPException):
    """Base security exception"""
    pass


class AuthenticationException(SecurityException):
    """Authentication failed exception"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationException(SecurityException):
    """Authorization failed exception"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class RateLimitException(SecurityException):
    """Rate limit exceeded exception"""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )
