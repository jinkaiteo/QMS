# EDMS Models - Phase 2
# Electronic Document Management System models

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Float,
    ForeignKey, Table, ARRAY, BigInteger, LargeBinary
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from typing import List, Optional
from datetime import datetime, date

from app.models.base import BaseModel


class DocumentType(BaseModel):
    __tablename__ = "document_types"

    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    prefix = Column(String(10), comment="For document numbering")
    description = Column(Text)
    template_file_path = Column(String(500))
    is_controlled = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True, nullable=False)
    retention_period_years = Column(Integer, default=7)

    # Relationships
    documents = relationship("Document", back_populates="document_type")


class DocumentCategory(BaseModel):
    __tablename__ = "document_categories"

    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("document_categories.id"))
    description = Column(Text)
    color = Column(String(7), comment="Hex color code")
    icon = Column(String(50))
    is_active = Column(Boolean, default=True, nullable=False)

    # Self-referential relationship for hierarchy
    parent = relationship("DocumentCategory", remote_side="DocumentCategory.id")
    children = relationship("DocumentCategory", back_populates="parent")
    
    # Documents in this category
    documents = relationship("Document", back_populates="category")


class Document(BaseModel):
    __tablename__ = "documents"

    document_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("document_categories.id"))
    source_type = Column(String(50), default="internal")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    current_version_id = Column(Integer, ForeignKey("document_versions.id"))
    status = Column(String(50), default="draft")
    keywords = Column(ARRAY(String), default=[])
    tags = Column(ARRAY(String), default=[])
    is_template = Column(Boolean, default=False)
    is_controlled = Column(Boolean, default=True)
    confidentiality_level = Column(String(50), default="internal")
    next_review_date = Column(Date)
    superseded_by = Column(Integer, ForeignKey("documents.id"))

    # Relationships
    document_type = relationship("DocumentType", back_populates="documents")
    category = relationship("DocumentCategory", back_populates="documents")
    author = relationship("User", foreign_keys=[author_id], back_populates="authored_documents")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_documents")
    versions = relationship("DocumentVersion", foreign_keys="[DocumentVersion.document_id]", back_populates="document")
    current_version = relationship("DocumentVersion", foreign_keys=[current_version_id])
    # workflows access through versions relationship
    
    # Document relationships
    parent_relationships = relationship(
        "DocumentRelationship", 
        foreign_keys="DocumentRelationship.parent_document_id",
        back_populates="parent_document"
    )
    child_relationships = relationship(
        "DocumentRelationship", 
        foreign_keys="DocumentRelationship.child_document_id",
        back_populates="child_document"
    )
    
    permissions = relationship("DocumentPermission", back_populates="document")


class DocumentVersion(BaseModel):
    __tablename__ = "document_versions"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(String(20), nullable=False)
    major_version = Column(Integer, nullable=False)
    minor_version = Column(Integer, nullable=False)
    is_draft = Column(Boolean, default=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(128), nullable=False, comment="SHA-256 hash")
    file_mime_type = Column(String(100), nullable=False)
    page_count = Column(Integer)
    word_count = Column(Integer)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    approver_id = Column(Integer, ForeignKey("users.id"))
    change_summary = Column(Text)
    reviewed_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    effective_date = Column(Date)
    expiry_date = Column(Date)
    status = Column(String(50), default="draft")

    # Relationships
    document = relationship("Document", foreign_keys=[document_id], back_populates="versions")
    author = relationship("User", foreign_keys=[author_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    approver = relationship("User", foreign_keys=[approver_id])
    workflows = relationship("DocumentWorkflow", back_populates="document_version")
    signatures = relationship("DigitalSignature", back_populates="document_version")
    comments = relationship("DocumentComment", back_populates="document_version")

    __table_args__ = (
        {"comment": "Document version history with file storage"},
    )


class DocumentWorkflow(BaseModel):
    __tablename__ = "document_workflows"

    document_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    workflow_type = Column(String(50), nullable=False)
    workflow_name = Column(String(255))
    current_state = Column(String(50), default="pending")
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    due_date = Column(Date)
    priority = Column(Integer, default=3)  # 1=High, 2=Medium, 3=Low
    comments = Column(Text)
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    document_version = relationship("DocumentVersion", back_populates="workflows")
    initiator = relationship("User", foreign_keys=[initiated_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    steps = relationship("WorkflowStep", back_populates="workflow")


class WorkflowStep(BaseModel):
    __tablename__ = "workflow_steps"

    workflow_id = Column(Integer, ForeignKey("document_workflows.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(255), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    required = Column(Boolean, default=True)
    completed_by = Column(Integer, ForeignKey("users.id"))
    completed_at = Column(DateTime(timezone=True))
    due_date = Column(Date)
    comments = Column(Text)
    status = Column(String(50), default="pending")

    # Relationships
    workflow = relationship("DocumentWorkflow", back_populates="steps")
    assignee = relationship("User", foreign_keys=[assigned_to])
    completer = relationship("User", foreign_keys=[completed_by])


class DigitalSignature(BaseModel):
    __tablename__ = "digital_signatures"

    document_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    signer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    signature_type = Column(String(50), nullable=False)
    signature_meaning = Column(String(255), nullable=False)
    signature_hash = Column(String(512), nullable=False)
    certificate_hash = Column(String(256))
    certificate_subject = Column(String(500))
    timestamp_authority_response = Column(Text, comment="TSA response for long-term validity")
    signed_at = Column(DateTime(timezone=True), default=func.now())
    ip_address = Column(INET)
    user_agent = Column(Text)
    is_valid = Column(Boolean, default=True)

    # Relationships
    document_version = relationship("DocumentVersion", back_populates="signatures")
    signer = relationship("User", back_populates="digital_signatures")


class DocumentRelationship(BaseModel):
    __tablename__ = "document_relationships"

    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    child_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    parent_document = relationship("Document", foreign_keys=[parent_document_id])
    child_document = relationship("Document", foreign_keys=[child_document_id])
    creator = relationship("User", foreign_keys=[created_by])


class DocumentPermission(BaseModel):
    __tablename__ = "document_permissions"

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    permission_type = Column(String(50), nullable=False)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)

    # Relationships
    document = relationship("Document", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role", foreign_keys=[role_id])
    granter = relationship("User", foreign_keys=[granted_by])


class DocumentComment(BaseModel):
    __tablename__ = "document_comments"

    document_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("document_comments.id"))
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    position_x = Column(Float)
    position_y = Column(Float)
    highlight_text = Column(Text)
    comment_type = Column(String(50), default="general")
    status = Column(String(50), default="open")

    # Relationships
    document_version = relationship("DocumentVersion", back_populates="comments")
    user = relationship("User", back_populates="document_comments")
    parent_comment = relationship("DocumentComment", remote_side="DocumentComment.id")
    replies = relationship("DocumentComment", back_populates="parent_comment")


# Update User model relationships (to be added to user.py)
"""
Add these relationships to the User model:

    # EDMS relationships
    authored_documents = relationship("Document", foreign_keys="Document.author_id", back_populates="author")
    owned_documents = relationship("Document", foreign_keys="Document.owner_id", back_populates="owner")
    digital_signatures = relationship("DigitalSignature", back_populates="signer")
    document_comments = relationship("DocumentComment", back_populates="user")
"""