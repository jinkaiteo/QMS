# EDMS Schemas - Phase 2
# Pydantic schemas for EDMS API endpoints

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


class DocumentStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    OBSOLETE = "obsolete"
    SUPERSEDED = "superseded"


class WorkflowStateEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class SignatureTypeEnum(str, Enum):
    AUTHOR = "author"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    WITNESS = "witness"


# Document Type schemas
class DocumentTypeBase(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    prefix: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None
    is_controlled: bool = True
    retention_period_years: int = 7


class DocumentTypeCreate(DocumentTypeBase):
    pass


class DocumentTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    prefix: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None
    is_controlled: Optional[bool] = None
    retention_period_years: Optional[int] = None


class DocumentType(DocumentTypeBase):
    id: int
    uuid: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Document Category schemas
class DocumentCategoryBase(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class DocumentCategoryCreate(DocumentCategoryBase):
    pass


class DocumentCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class DocumentCategory(DocumentCategoryBase):
    id: int
    uuid: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Document schemas
class DocumentBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    document_type_id: int
    category_id: Optional[int] = None
    keywords: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    confidentiality_level: str = Field(default="internal", pattern=r"^(public|internal|confidential|restricted)$")


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category_id: Optional[int] = None
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    confidentiality_level: Optional[str] = Field(None, pattern=r"^(public|internal|confidential|restricted)$")


class UserInfo(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    
    class Config:
        from_attributes = True


class DocumentVersion(BaseModel):
    id: int
    uuid: str
    version_number: str
    major_version: int
    minor_version: int
    is_draft: bool
    file_name: str
    file_size: int
    file_mime_type: str
    page_count: Optional[int]
    word_count: Optional[int]
    change_summary: Optional[str]
    reviewed_at: Optional[datetime]
    approved_at: Optional[datetime]
    effective_date: Optional[date]
    expiry_date: Optional[date]
    status: DocumentStatusEnum
    created_at: datetime
    author: Optional[UserInfo]
    reviewer: Optional[UserInfo]
    approver: Optional[UserInfo]
    
    class Config:
        from_attributes = True


class Document(DocumentBase):
    id: int
    uuid: str
    document_number: str
    source_type: str
    status: DocumentStatusEnum
    is_template: bool
    is_controlled: bool
    next_review_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    document_type: DocumentType
    category: Optional[DocumentCategory]
    author: UserInfo
    owner: Optional[UserInfo]
    current_version: Optional[DocumentVersion]
    
    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    id: int
    uuid: str
    document_number: str
    title: str
    status: DocumentStatusEnum
    document_type: DocumentType
    category: Optional[DocumentCategory]
    author: UserInfo
    current_version: Optional[str]
    effective_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    
    class Config:
        from_attributes = True


class DocumentSearchRequest(BaseModel):
    query: Optional[str] = None
    document_type_id: Optional[int] = None
    category_id: Optional[int] = None
    status: Optional[DocumentStatusEnum] = None
    author_id: Optional[int] = None
    created_from: Optional[date] = None
    created_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class DocumentSearchResponse(BaseModel):
    items: List[DocumentList]
    total: int
    page: int
    per_page: int
    pages: int


# Workflow schemas
class WorkflowStepBase(BaseModel):
    step_name: str = Field(..., max_length=255)
    assigned_to: int
    required: bool = True
    due_date: Optional[date] = None


class WorkflowStep(WorkflowStepBase):
    id: int
    uuid: str
    step_number: int
    completed_by: Optional[int]
    completed_at: Optional[datetime]
    comments: Optional[str]
    status: WorkflowStateEnum
    created_at: datetime
    assignee: UserInfo
    completer: Optional[UserInfo]
    
    class Config:
        from_attributes = True


class DocumentWorkflowBase(BaseModel):
    workflow_type: str = Field(..., max_length=50)
    workflow_name: Optional[str] = Field(None, max_length=255)
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    priority: int = Field(default=3, ge=1, le=3)
    comments: Optional[str] = None


class DocumentWorkflowCreate(DocumentWorkflowBase):
    document_version_id: int


class DocumentWorkflow(DocumentWorkflowBase):
    id: int
    uuid: str
    document_version_id: int
    current_state: WorkflowStateEnum
    initiated_by: int
    completed_at: Optional[datetime]
    created_at: datetime
    
    # Relationships
    initiator: UserInfo
    assignee: Optional[UserInfo]
    steps: List[WorkflowStep]
    
    class Config:
        from_attributes = True


class StartReviewRequest(BaseModel):
    reviewer_id: int
    due_date: Optional[date] = None
    comments: Optional[str] = None


class CompleteReviewRequest(BaseModel):
    approved: bool
    comments: Optional[str] = None


class ApproveDocumentRequest(BaseModel):
    effective_date: date
    comments: Optional[str] = None


# Digital Signature schemas
class DigitalSignature(BaseModel):
    id: int
    uuid: str
    signature_type: SignatureTypeEnum
    signature_meaning: str
    signed_at: datetime
    is_valid: bool
    signer: UserInfo
    
    class Config:
        from_attributes = True


# Comment schemas
class DocumentCommentBase(BaseModel):
    content: str = Field(..., min_length=1)
    page_number: Optional[int] = Field(None, ge=1)
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    highlight_text: Optional[str] = None
    comment_type: str = Field(default="general", pattern=r"^(general|review|approval|suggestion)$")
    parent_comment_id: Optional[int] = None


class DocumentCommentCreate(DocumentCommentBase):
    pass


class DocumentCommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = Field(None, pattern=r"^(open|addressed|resolved|dismissed)$")


class DocumentComment(DocumentCommentBase):
    id: int
    uuid: str
    status: str
    created_at: datetime
    updated_at: datetime
    user: UserInfo
    replies: List['DocumentComment'] = []
    
    class Config:
        from_attributes = True


# File upload schemas
class FileUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[int] = None
    document_number: Optional[str] = None


class DownloadRequest(BaseModel):
    version_id: Optional[int] = None
    download_type: str = Field(default="original", pattern=r"^(original|official_pdf|annotated)$")


# Update forward references
DocumentComment.model_rebuild()