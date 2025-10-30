# QMS User Models
# Phase 1: User management models for authentication and authorization

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import BaseModel


class UserStatus(str, enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    PENDING = "pending"


# Create PostgreSQL ENUM type that matches database values
user_status_enum = ENUM('active', 'inactive', 'locked', 'pending', name="user_status", create_type=False)


class Organization(BaseModel):
    """Organization/Company model"""
    
    __tablename__ = "organizations"
    
    name = Column(String(255), nullable=False, comment="Organization name")
    code = Column(String(50), unique=True, nullable=False, comment="Organization code")
    address = Column(Text, comment="Organization address")
    phone = Column(String(50), comment="Organization phone number")
    email = Column(String(255), comment="Organization email")
    website = Column(String(255), comment="Organization website")
    regulatory_license = Column(String(100), comment="Regulatory license number")
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    departments = relationship("Department", back_populates="organization")
    users = relationship("User", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization(name={self.name}, code={self.code})>"


class Department(BaseModel):
    """Department model"""
    
    __tablename__ = "departments"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False, comment="Department name")
    code = Column(String(50), nullable=False, comment="Department code")
    description = Column(Text, comment="Department description")
    manager_id = Column(Integer, ForeignKey("users.id"), comment="Department manager")
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="departments")
    manager = relationship("User", foreign_keys=[manager_id], post_update=True)
    users = relationship("User", foreign_keys="User.department_id", back_populates="department")
    
    def __repr__(self):
        return f"<Department(name={self.name}, code={self.code})>"


class User(BaseModel):
    """User model for authentication and user management"""
    
    __tablename__ = "users"
    
    # Basic Information
    username = Column(String(100), unique=True, nullable=False, index=True, comment="Unique username")
    email = Column(String(255), unique=True, nullable=False, index=True, comment="User email address")
    password_hash = Column(String(255), comment="Hashed password")
    first_name = Column(String(100), nullable=False, comment="User first name")
    last_name = Column(String(100), nullable=False, comment="User last name")
    employee_id = Column(String(50), unique=True, comment="Employee ID")
    
    # Organization Information
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    manager_id = Column(Integer, ForeignKey("users.id"), comment="Direct manager")
    
    # Contact Information
    phone = Column(String(50), comment="Phone number")
    
    # Authentication & Security
    entra_id = Column(String(255), comment="Microsoft Entra ID for SSO")
    digital_signature_cert = Column(Text, comment="Base64 encoded digital certificate")
    last_login = Column(DateTime(timezone=True), comment="Last login timestamp")
    login_count = Column(Integer, default=0, comment="Total login count")
    failed_login_attempts = Column(Integer, default=0, comment="Failed login attempts")
    account_locked_until = Column(DateTime(timezone=True), comment="Account lock expiration")
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Password last changed")
    must_change_password = Column(Boolean, default=False, comment="Force password change on next login")
    
    # Two-Factor Authentication
    two_factor_enabled = Column(Boolean, default=False, comment="2FA enabled flag")
    two_factor_secret = Column(String(255), comment="2FA secret key")
    
    # Status
    status = Column(user_status_enum, default=UserStatus.PENDING, nullable=False, comment="User account status")
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    department = relationship("Department", foreign_keys=[department_id], back_populates="users")
    manager = relationship("User", remote_side="User.id")
    
    # Role assignments
    user_roles = relationship("UserRole", foreign_keys="[UserRole.user_id]", back_populates="user", cascade="all, delete-orphan")
    
    # Sessions
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    # Password history
    password_history = relationship("PasswordHistory", back_populates="user", cascade="all, delete-orphan")
    
    # EDMS relationships (Phase 2)
    authored_documents = relationship("Document", foreign_keys="Document.author_id", back_populates="author")
    owned_documents = relationship("Document", foreign_keys="Document.owner_id", back_populates="owner")
    digital_signatures = relationship("DigitalSignature", back_populates="signer")
    document_comments = relationship("DocumentComment", back_populates="user")
    
    # Note: QRM and Training relationships will be added after all models are properly imported
    # This avoids forward reference issues in SQLAlchemy
    
    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self):
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE and not self.is_deleted
    
    @property
    def is_locked(self):
        """Check if user account is locked"""
        if self.status == UserStatus.LOCKED:
            return True
        
        if self.account_locked_until:
            from datetime import datetime
            return datetime.utcnow() < self.account_locked_until.replace(tzinfo=None)
        
        return False
    
    def get_permissions(self):
        """Get all user permissions from roles"""
        permissions = set()
        for user_role in self.user_roles:
            if user_role.is_active and user_role.role.is_active:
                role_permissions = user_role.role.permissions or []
                permissions.update(role_permissions)
        return list(permissions)
    
    def has_permission(self, permission: str, module: str = None) -> bool:
        """Check if user has specific permission"""
        for user_role in self.user_roles:
            if user_role.is_active and user_role.role.is_active:
                if module and user_role.role.module != module:
                    continue
                
                role_permissions = user_role.role.permissions or []
                if permission in role_permissions:
                    return True
        
        return False
    
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"


class Role(BaseModel):
    """Role model for permissions and access control"""
    
    __tablename__ = "roles"
    
    # Override BaseModel field that doesn't exist in database
    is_deleted = None
    
    name = Column(String(100), unique=True, nullable=False, comment="Role name")
    display_name = Column(String(255), nullable=False, comment="Human-readable role name")
    description = Column(Text, comment="Role description")
    module = Column(String(50), nullable=False, comment="Module this role applies to")
    permissions = Column(JSONB, nullable=False, comment="List of permissions")
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user_roles = relationship("UserRole", foreign_keys="[UserRole.role_id]", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role(name={self.name}, module={self.module})>"


class UserRole(BaseModel):
    """User-Role assignment model"""
    
    __tablename__ = "user_roles"
    
    # Override BaseModel fields that don't exist in the actual database table
    uuid = None
    created_at = None
    updated_at = None
    version = None
    is_deleted = None
    
    # The actual database has 'id' as primary key, not composite key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), comment="User who assigned the role")
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Role assignment timestamp")
    valid_from = Column(DateTime(timezone=True), server_default=func.now(), comment="Role validity start date")
    valid_until = Column(DateTime(timezone=True), comment="Role validity end date")
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    
    @property
    def is_valid(self):
        """Check if role assignment is currently valid"""
        if not self.is_active:
            return False
        
        from datetime import datetime
        now = datetime.utcnow()
        
        if self.valid_from and now < self.valid_from.replace(tzinfo=None):
            return False
        
        if self.valid_until and now > self.valid_until.replace(tzinfo=None):
            return False
        
        return True
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class UserSession(BaseModel):
    """User session model for tracking active sessions"""
    
    __tablename__ = "user_sessions"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, comment="Session token")
    refresh_token = Column(String(255), comment="Refresh token")
    ip_address = Column(String(45), comment="Client IP address")
    user_agent = Column(Text, comment="Client user agent")
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), comment="Last activity timestamp")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="Session expiration time")
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    @property
    def is_expired(self):
        """Check if session is expired"""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, token={self.session_token[:8]}...)>"


class PasswordHistory(BaseModel):
    """Password history model for compliance"""
    
    __tablename__ = "password_history"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    password_hash = Column(String(255), nullable=False, comment="Historical password hash")
    
    # Relationships
    user = relationship("User", back_populates="password_history")
    
    def __repr__(self):
        return f"<PasswordHistory(user_id={self.user_id})>"
