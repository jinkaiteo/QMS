# QRM Schemas - Phase 3
# Pydantic schemas for QRM API endpoints

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


# Enums for validation
class QualityEventSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFORMATIONAL = "informational"


class QualityEventStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CAPA_PENDING = "capa_pending"
    CAPA_IN_PROGRESS = "capa_in_progress"
    UNDER_REVIEW = "under_review"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class CAPAType(str, Enum):
    CORRECTIVE = "corrective"
    PREVENTIVE = "preventive"
    IMPROVEMENT = "improvement"


class CAPAStatus(str, Enum):
    PLANNING = "planning"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFICATION_PENDING = "verification_pending"
    VERIFIED = "verified"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ChangeType(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    EMERGENCY = "emergency"


# Quality Event Type schemas
class QualityEventTypeBase(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    severity_levels: List[str] = []
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class QualityEventTypeCreate(QualityEventTypeBase):
    pass


class QualityEventType(QualityEventTypeBase):
    id: int
    uuid: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# User info for relationships
class UserInfo(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    
    class Config:
        from_attributes = True


class DepartmentInfo(BaseModel):
    id: int
    name: str
    code: str
    
    class Config:
        from_attributes = True


# Quality Event schemas
class QualityEventBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: str = Field(..., min_length=10)
    event_type_id: int
    severity: QualityEventSeverity
    occurred_at: datetime
    priority: int = Field(default=3, ge=1, le=3)
    source: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    department_id: Optional[int] = None
    
    # Product/Process impact
    product_affected: Optional[str] = Field(None, max_length=255)
    batch_lot_numbers: List[str] = []
    processes_affected: List[str] = []
    
    # Impact assessment
    patient_safety_impact: bool = False
    product_quality_impact: bool = False
    regulatory_impact: bool = False
    business_impact_severity: Optional[str] = Field(None, pattern=r"^(low|medium|high|critical)$")
    estimated_cost: Optional[float] = Field(None, ge=0)
    
    # Requirements
    investigation_required: bool = True
    capa_required: bool = False
    regulatory_reporting_required: bool = False


class QualityEventCreate(QualityEventBase):
    pass


class QualityEventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, min_length=10)
    severity: Optional[QualityEventSeverity] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    location: Optional[str] = Field(None, max_length=255)
    department_id: Optional[int] = None
    
    # Impact updates
    patient_safety_impact: Optional[bool] = None
    product_quality_impact: Optional[bool] = None
    regulatory_impact: Optional[bool] = None
    business_impact_severity: Optional[str] = Field(None, pattern=r"^(low|medium|high|critical)$")
    estimated_cost: Optional[float] = Field(None, ge=0)
    
    # Resolution fields
    root_cause: Optional[str] = None
    immediate_actions: Optional[str] = None
    containment_actions: Optional[str] = None


class QualityEvent(QualityEventBase):
    id: int
    uuid: str
    event_number: str
    status: QualityEventStatus
    discovered_at: datetime
    
    # Dates
    investigation_due_date: Optional[date]
    capa_due_date: Optional[date]
    target_closure_date: Optional[date]
    actual_closure_date: Optional[date]
    
    # Resolution
    root_cause: Optional[str]
    immediate_actions: Optional[str]
    containment_actions: Optional[str]
    
    # Relationships
    event_type: QualityEventType
    department: Optional[DepartmentInfo]
    reporter: UserInfo
    assignee: Optional[UserInfo]
    investigator: Optional[UserInfo]
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QualityEventList(BaseModel):
    id: int
    uuid: str
    event_number: str
    title: str
    severity: QualityEventSeverity
    status: QualityEventStatus
    occurred_at: datetime
    event_type: QualityEventType
    reporter: UserInfo
    department: Optional[DepartmentInfo]
    investigation_due_date: Optional[date]
    created_at: datetime
    
    class Config:
        from_attributes = True


# CAPA schemas
class CAPABase(BaseModel):
    title: str = Field(..., max_length=500)
    description: str = Field(..., min_length=10)
    capa_type: CAPAType
    problem_statement: str = Field(..., min_length=10)
    proposed_solution: str = Field(..., min_length=10)
    target_completion_date: date
    priority: int = Field(default=3, ge=1, le=3)
    
    # Optional fields
    action_category: Optional[str] = Field(None, max_length=100)
    responsible_department_id: Optional[int] = None
    assigned_to: Optional[int] = None
    root_cause: Optional[str] = None
    implementation_plan: Optional[str] = None
    success_criteria: Optional[str] = None
    target_start_date: Optional[date] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    resources_required: Optional[str] = None
    risk_level: Optional[str] = Field(None, pattern=r"^(low|medium|high|critical)$")
    verification_method: Optional[str] = None
    verification_criteria: Optional[str] = None
    training_required: bool = False


class CAPACreate(CAPABase):
    owner_id: int
    quality_event_id: Optional[int] = None
    investigation_id: Optional[int] = None


class CAPAUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, min_length=10)
    problem_statement: Optional[str] = Field(None, min_length=10)
    proposed_solution: Optional[str] = Field(None, min_length=10)
    target_completion_date: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    
    implementation_plan: Optional[str] = None
    success_criteria: Optional[str] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    resources_required: Optional[str] = None
    risk_level: Optional[str] = Field(None, pattern=r"^(low|medium|high|critical)$")
    verification_method: Optional[str] = None
    verification_criteria: Optional[str] = None


class CAPA(CAPABase):
    id: int
    uuid: str
    capa_number: str
    status: CAPAStatus
    completion_percentage: int
    
    # Dates
    actual_start_date: Optional[date]
    actual_completion_date: Optional[date]
    verification_due_date: Optional[date]
    verification_completed_date: Optional[date]
    
    # Cost tracking
    actual_cost: Optional[float]
    
    # Verification
    effectiveness_confirmed: bool
    verification_comments: Optional[str]
    
    # Approval
    reviewed_at: Optional[datetime]
    approved_at: Optional[datetime]
    
    # Relationships
    owner: UserInfo
    responsible_department: Optional[DepartmentInfo]
    assignee: Optional[UserInfo]
    reviewer: Optional[UserInfo]
    approver: Optional[UserInfo]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# CAPA Action schemas
class CAPAActionBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    due_date: date
    department_id: Optional[int] = None
    depends_on: List[int] = []
    verification_required: bool = False


class CAPAActionCreate(CAPAActionBase):
    assigned_to: int


class CAPAActionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    completion_evidence: Optional[str] = None


class CAPAAction(CAPAActionBase):
    id: int
    uuid: str
    action_number: str
    status: str
    completion_percentage: int
    completed_date: Optional[date]
    completion_evidence: Optional[str]
    verified_at: Optional[datetime]
    
    # Relationships
    assignee: UserInfo
    department: Optional[DepartmentInfo]
    verifier: Optional[UserInfo]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Search and filter schemas
class QualityEventSearchRequest(BaseModel):
    query: Optional[str] = None
    event_type_id: Optional[int] = None
    severity: Optional[QualityEventSeverity] = None
    status: Optional[QualityEventStatus] = None
    reporter_id: Optional[int] = None
    department_id: Optional[int] = None
    occurred_from: Optional[date] = None
    occurred_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class CAPASearchRequest(BaseModel):
    query: Optional[str] = None
    capa_type: Optional[CAPAType] = None
    status: Optional[CAPAStatus] = None
    owner_id: Optional[int] = None
    department_id: Optional[int] = None
    due_from: Optional[date] = None
    due_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class QualityEventSearchResponse(BaseModel):
    items: List[QualityEventList]
    total: int
    page: int
    per_page: int
    pages: int


class CAPASearchResponse(BaseModel):
    items: List[CAPA]
    total: int
    page: int
    per_page: int
    pages: int


# Assignment and workflow schemas
class AssignInvestigatorRequest(BaseModel):
    investigator_id: int
    due_date: Optional[date] = None
    comments: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: str
    comments: Optional[str] = None


class ApproveCAPARequest(BaseModel):
    comments: Optional[str] = None


class VerifyEffectivenessRequest(BaseModel):
    effectiveness_confirmed: bool
    verification_comments: str


class CompleteActionRequest(BaseModel):
    completion_evidence: str