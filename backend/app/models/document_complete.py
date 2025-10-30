"""
Complete Document Management Models
Extended EDMS models with file storage and workflow support
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import BaseModel


class DocumentStatus(str, enum.Enum):
    """Document status enumeration"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    RETIRED = "retired"
    SUPERSEDED = "superseded"


class ApprovalStatus(str, enum.Enum):
    """Approval status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"


class Document(BaseModel):
    """Extended document model with file storage"""
    __tablename__ = "documents"
    __table_args__ = {'extend_existing': True}
    
    # Basic document information
    title = Column(String(500), nullable=False)
    description = Column(Text)
    document_number = Column(String(100), unique=True)
    
    # File storage information
    file_path = Column(String(500))  # MinIO object path
    file_name = Column(String(255))  # Original filename
    file_size = Column(Integer)      # File size in bytes
    mime_type = Column(String(100))  # MIME type
    file_hash = Column(String(64))   # SHA-256 hash for integrity
    
    # Document classification
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("document_categories.id"))
    
    # Workflow and status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)
    effective_date = Column(DateTime)
    expiry_date = Column(DateTime)
    review_due_date = Column(DateTime)
    
    # Ownership and control
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_owner_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    
    # Version control
    current_version = Column(String(20), default="1.0")
    supersedes_document_id = Column(Integer, ForeignKey("documents.id"))
    
    # Compliance
    is_controlled = Column(Boolean, default=True)
    requires_training = Column(Boolean, default=False)
    confidentiality_level = Column(String(50), default="internal")
    
    # Relationships
    document_type = relationship("DocumentType", back_populates="documents")
    category = relationship("DocumentCategory", back_populates="documents")
    created_by = relationship("User", foreign_keys=[created_by_id])
    current_owner = relationship("User", foreign_keys=[current_owner_id])
    supersedes_document = relationship("Document", remote_side="Document.id")
    
    # Document workflow relationships
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    reviews = relationship("DocumentReview", back_populates="document", cascade="all, delete-orphan")
    approvals = relationship("DocumentApproval", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"


class DocumentVersion(BaseModel):
    """Document version history"""
    __tablename__ = "document_versions"
    __table_args__ = {'extend_existing': True}
    
    # Version information
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(String(20), nullable=False)
    
    # File information for this version
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    file_hash = Column(String(64))
    
    # Version metadata
    change_summary = Column(Text)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by_id = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    # Status
    is_current = Column(Boolean, default=False)
    
    # Relationships
    document = relationship("Document", back_populates="versions")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    def __repr__(self):
        return f"<DocumentVersion(document_id={self.document_id}, version='{self.version_number}')>"


class DocumentReview(BaseModel):
    """Document review assignments and tracking"""
    __tablename__ = "document_reviews"
    
    # Review assignment
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Review details
    review_type = Column(String(50), default="standard")  # standard, expedited, technical
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Review results
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    comments = Column(Text)
    recommendations = Column(Text)
    
    # Relationships
    document = relationship("Document", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    
    def __repr__(self):
        return f"<DocumentReview(document_id={self.document_id}, reviewer_id={self.reviewer_id})>"


class DocumentApproval(BaseModel):
    """Document approval workflow"""
    __tablename__ = "document_approvals"
    
    # Approval assignment
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approval_level = Column(Integer, default=1)  # Multi-level approval support
    
    # Approval details
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Approval results
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    comments = Column(Text)
    digital_signature = Column(Text)  # Digital signature data
    
    # Relationships
    document = relationship("Document", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approver_id])
    
    def __repr__(self):
        return f"<DocumentApproval(document_id={self.document_id}, approver_id={self.approver_id})>"


class DocumentAccess(BaseModel):
    """Document access control and audit"""
    __tablename__ = "document_access"
    
    # Access details
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Access type and metadata
    access_type = Column(String(50))  # view, download, edit, print
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(255))
    
    # Timestamps
    accessed_at = Column(DateTime, default=func.now())
    
    # Relationships
    document = relationship("Document")
    user = relationship("User")
    
    def __repr__(self):
        return f"<DocumentAccess(document_id={self.document_id}, user_id={self.user_id}, type='{self.access_type}')>"


class DocumentTemplate(BaseModel):
    """Document templates for standardized document creation"""
    __tablename__ = "document_templates"
    
    # Template information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    
    # Template file
    template_path = Column(String(500))
    template_version = Column(String(20), default="1.0")
    
    # Template metadata
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # Relationships
    document_type = relationship("DocumentType")
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<DocumentTemplate(id={self.id}, name='{self.name}')>"