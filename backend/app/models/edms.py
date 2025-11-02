from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel

class DocumentType(BaseModel):
    __tablename__ = "document_types"
    
    # Override BaseModel fields that don't exist in the database
    is_deleted = None
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    prefix = Column(String(10))
    is_active = Column(Boolean, default=True)

class DocumentCategory(BaseModel):
    __tablename__ = "document_categories"
    
    # Override BaseModel fields that don't exist in the database
    is_deleted = None
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("document_categories.id"))
    is_active = Column(Boolean, default=True)

class Document(BaseModel):
    __tablename__ = "documents"

    # Basic document info (matching actual database table)
    document_number = Column(String(100), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("document_categories.id"))
    source_type = Column(String(50), default="internal")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    current_version_id = Column(Integer, ForeignKey("document_versions.id"))
    status = Column(String(50), default="draft")
    keywords = Column(Text)  # Array in DB, simplified here
    tags = Column(Text)      # Array in DB, simplified here
    is_template = Column(Boolean, default=False)
    is_controlled = Column(Boolean, default=True)
    confidentiality_level = Column(String(50), default="internal")
    next_review_date = Column(Date)
    superseded_by = Column(Integer, ForeignKey("documents.id"))
    
    # Relationships (simplified to avoid circular references)
    document_type = relationship("DocumentType")
    category = relationship("DocumentCategory")
    # author = relationship("User", foreign_keys=[author_id])
    # owner = relationship("User", foreign_keys=[owner_id])
    # current_version = relationship("DocumentVersion", foreign_keys=[current_version_id], post_update=True)
    # superseded_by_doc = relationship("Document", remote_side="Document.id")
    # versions = relationship("DocumentVersion", foreign_keys="DocumentVersion.document_id", back_populates="document")
    
    @classmethod
    def get_by_number(cls, db, document_number: str):
        return db.query(cls).filter(cls.document_number == document_number).first()
    
    @classmethod
    def get_by_type_and_category(cls, db, document_type_id: int, category_id: int = None):
        query = db.query(cls).filter(cls.document_type_id == document_type_id)
        if category_id:
            query = query.filter(cls.category_id == category_id)
        return query.all()


class DocumentVersion(BaseModel):
    __tablename__ = "document_versions"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(String(20), nullable=False)
    major_version = Column(Integer, default=1)
    minor_version = Column(Integer, default=0)
    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size = Column(Integer)
    file_hash = Column(String(64))
    file_mime_type = Column(String(100))
    page_count = Column(Integer)
    word_count = Column(Integer)
    status = Column(String(50), default="draft")
    is_draft = Column(Boolean, default=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    approver_id = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    effective_date = Column(Date)
    
    # Relationships (simplified to avoid circular references)
    # document = relationship("Document", back_populates="versions")
    author = relationship("User", foreign_keys=[author_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    approver = relationship("User", foreign_keys=[approver_id])


class DocumentWorkflow(BaseModel):
    __tablename__ = "document_workflows"
    
    document_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    workflow_type = Column(String(50), nullable=False)  # review, approval, change_control
    workflow_name = Column(String(200))
    current_state = Column(String(50), default="pending")  # pending, in_progress, completed, cancelled
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    due_date = Column(Date)
    completed_at = Column(DateTime(timezone=True))
    comments = Column(Text)
    priority = Column(Integer, default=2)  # 1=high, 2=medium, 3=low
    
    # Relationships
    document_version = relationship("DocumentVersion")
    initiator = relationship("User", foreign_keys=[initiated_by])
    assignee = relationship("User", foreign_keys=[assigned_to])


class WorkflowStep(BaseModel):
    __tablename__ = "workflow_steps"
    
    workflow_id = Column(Integer, ForeignKey("document_workflows.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(200), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    due_date = Column(Date)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, skipped
    completed_by = Column(Integer, ForeignKey("users.id"))
    completed_at = Column(DateTime(timezone=True))
    comments = Column(Text)
    
    # Relationships
    workflow = relationship("DocumentWorkflow")
    assignee = relationship("User", foreign_keys=[assigned_to])
    completer = relationship("User", foreign_keys=[completed_by])


class DigitalSignature(BaseModel):
    __tablename__ = "digital_signatures"
    
    document_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    signer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    signature_type = Column(String(50), nullable=False)  # author, reviewer, approver
    signature_meaning = Column(String(200))
    signature_hash = Column(String(256))  # Digital signature hash
    signed_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    document_version = relationship("DocumentVersion")
    signer = relationship("User")


class DocumentRelationship(BaseModel):
    __tablename__ = "document_relationships"
    
    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    child_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # supersedes, references, depends_on
    
    # Relationships
    parent_document = relationship("Document", foreign_keys=[parent_document_id])
    child_document = relationship("Document", foreign_keys=[child_document_id])


class DocumentPermission(BaseModel):
    __tablename__ = "document_permissions"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    permission_type = Column(String(50), nullable=False)  # read, write, review, approve
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    document = relationship("Document")
    user = relationship("User", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by])


class DocumentComment(BaseModel):
    __tablename__ = "document_comments"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    comment_type = Column(String(50), default="general")  # general, review, approval
    
    # Relationships
    document = relationship("Document")
    user = relationship("User")