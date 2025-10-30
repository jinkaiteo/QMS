"""
Training Management System (TRM) Schemas
Phase 4 Implementation - QMS Platform v3.0

Pydantic schemas for API request/response validation
and data serialization for the training management module.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from app.models.training import (
    TrainingType, TrainingStatus, DeliveryMethod, 
    CompetencyLevel
)


# Request/Response Base Classes
class TrainingProgramBase(BaseModel):
    code: str = Field(..., max_length=50, description="Unique program code")
    title: str = Field(..., max_length=200, description="Program title")
    description: Optional[str] = Field(None, description="Program description")
    training_type: TrainingType
    delivery_method: DeliveryMethod
    duration_hours: Optional[float] = Field(None, ge=0, description="Duration in hours")
    validity_months: Optional[int] = Field(None, ge=1, description="Certification validity")
    learning_objectives: Optional[List[str]] = Field(None, description="Learning objectives")
    prerequisites: Optional[List[str]] = Field(None, description="Prerequisites")
    materials_required: Optional[List[str]] = Field(None, description="Required materials")
    regulatory_requirement: bool = Field(False, description="Is regulatory required")
    approval_required: bool = Field(True, description="Requires approval")
    version: str = Field("1.0", description="Program version")


class TrainingProgramCreate(TrainingProgramBase):
    effective_date: Optional[datetime] = Field(None, description="Effective date")


class TrainingProgramUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    training_type: Optional[TrainingType] = None
    delivery_method: Optional[DeliveryMethod] = None
    duration_hours: Optional[float] = Field(None, ge=0)
    validity_months: Optional[int] = Field(None, ge=1)
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    materials_required: Optional[List[str]] = None
    regulatory_requirement: Optional[bool] = None
    approval_required: Optional[bool] = None
    retirement_date: Optional[datetime] = None


class TrainingProgram(TrainingProgramBase):
    id: int
    effective_date: datetime
    retirement_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Training Session Schemas
class TrainingSessionBase(BaseModel):
    session_code: str = Field(..., max_length=50, description="Unique session code")
    start_datetime: datetime = Field(..., description="Session start time")
    end_datetime: datetime = Field(..., description="Session end time")
    location: Optional[str] = Field(None, max_length=200, description="Location")
    max_participants: Optional[int] = Field(None, ge=1, description="Maximum participants")
    min_participants: Optional[int] = Field(None, ge=1, description="Minimum participants")
    instructor_id: Optional[int] = Field(None, description="Instructor user ID")
    instructor_notes: Optional[str] = Field(None, description="Instructor notes")

    @validator('end_datetime')
    def end_after_start(cls, v, values):
        if 'start_datetime' in values and v <= values['start_datetime']:
            raise ValueError('End time must be after start time')
        return v


class TrainingSessionCreate(TrainingSessionBase):
    program_id: int = Field(..., description="Training program ID")


class TrainingSessionUpdate(BaseModel):
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=200)
    max_participants: Optional[int] = Field(None, ge=1)
    min_participants: Optional[int] = Field(None, ge=1)
    instructor_id: Optional[int] = None
    instructor_notes: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(scheduled|in_progress|completed|cancelled)$")
    completion_notes: Optional[str] = None


class TrainingSession(TrainingSessionBase):
    id: int
    program_id: int
    status: str
    completion_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships
    program: Optional[TrainingProgram] = None
    
    class Config:
        from_attributes = True


# Employee Training Schemas
class EmployeeTrainingBase(BaseModel):
    due_date: Optional[datetime] = Field(None, description="Training due date")
    reason: Optional[str] = Field(None, max_length=500, description="Assignment reason")


class EmployeeTrainingCreate(EmployeeTrainingBase):
    employee_id: int = Field(..., description="Employee user ID")
    program_id: int = Field(..., description="Training program ID")


class EmployeeTrainingUpdate(BaseModel):
    due_date: Optional[datetime] = None
    status: Optional[TrainingStatus] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    pass_fail: Optional[bool] = None
    employee_feedback: Optional[str] = None
    supervisor_notes: Optional[str] = None


class EmployeeTraining(EmployeeTrainingBase):
    id: int
    employee_id: int
    program_id: int
    assigned_date: datetime
    assigned_by_id: Optional[int]
    status: TrainingStatus
    start_date: Optional[datetime]
    completion_date: Optional[datetime]
    score: Optional[float]
    pass_fail: Optional[bool]
    certificate_issued: bool
    certificate_number: Optional[str]
    certification_date: Optional[datetime]
    expiry_date: Optional[datetime]
    employee_feedback: Optional[str]
    supervisor_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships (optional for performance)
    program: Optional[TrainingProgram] = None
    
    class Config:
        from_attributes = True


# Competency Schemas
class CompetencyBase(BaseModel):
    code: str = Field(..., max_length=50, description="Unique competency code")
    name: str = Field(..., max_length=200, description="Competency name")
    description: Optional[str] = Field(None, description="Competency description")
    category: Optional[str] = Field(None, max_length=100, description="Competency category")


class CompetencyCreate(CompetencyBase):
    pass


class CompetencyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)


class Competency(CompetencyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Competency Assessment Schemas
class CompetencyAssessmentBase(BaseModel):
    assessment_date: date = Field(..., description="Assessment date")
    current_level: CompetencyLevel = Field(..., description="Current competency level")
    target_level: Optional[CompetencyLevel] = Field(None, description="Target level")
    assessment_method: Optional[str] = Field(None, max_length=100, description="Assessment method")
    strengths: Optional[str] = Field(None, description="Identified strengths")
    improvement_areas: Optional[str] = Field(None, description="Areas for improvement")
    recommended_training: Optional[List[str]] = Field(None, description="Recommended training")
    next_assessment_date: Optional[date] = Field(None, description="Next assessment date")


class CompetencyAssessmentCreate(CompetencyAssessmentBase):
    employee_id: int = Field(..., description="Employee user ID")
    competency_id: int = Field(..., description="Competency ID")


class CompetencyAssessmentUpdate(BaseModel):
    current_level: Optional[CompetencyLevel] = None
    target_level: Optional[CompetencyLevel] = None
    assessment_method: Optional[str] = Field(None, max_length=100)
    strengths: Optional[str] = None
    improvement_areas: Optional[str] = None
    recommended_training: Optional[List[str]] = None
    next_assessment_date: Optional[date] = None


class CompetencyAssessment(CompetencyAssessmentBase):
    id: int
    employee_id: int
    competency_id: int
    assessor_id: int
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships
    competency: Optional[Competency] = None
    
    class Config:
        from_attributes = True


# Training Report Schemas
class TrainingComplianceReport(BaseModel):
    employee_id: int
    employee_name: str
    department: Optional[str]
    total_assigned: int
    completed: int
    overdue: int
    expiring_soon: int  # Within 30 days
    compliance_percentage: float
    
    class Config:
        from_attributes = True


class ProgramEffectivenessReport(BaseModel):
    program_id: int
    program_title: str
    total_participants: int
    completion_rate: float
    average_score: Optional[float]
    pass_rate: Optional[float]
    average_feedback_rating: Optional[float]
    
    class Config:
        from_attributes = True


class CompetencyGapReport(BaseModel):
    employee_id: int
    employee_name: str
    role: str
    competency_gaps: List[Dict[str, Any]]  # Competency name, required level, current level
    recommended_training: List[str]
    
    class Config:
        from_attributes = True


# Dashboard Schemas
class TrainingDashboard(BaseModel):
    total_programs: int
    active_programs: int
    total_employees: int
    employees_with_overdue_training: int
    overall_compliance_rate: float
    recent_completions: List[Dict[str, Any]]
    upcoming_sessions: List[Dict[str, Any]]
    expiring_certifications: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Bulk Operations
class BulkTrainingAssignment(BaseModel):
    program_id: int
    employee_ids: List[int] = Field(..., min_items=1, description="List of employee IDs")
    due_date: Optional[datetime] = None
    reason: Optional[str] = Field(None, max_length=500)
    
    class Config:
        from_attributes = True


class BulkTrainingAssignmentResult(BaseModel):
    successful_assignments: int
    failed_assignments: int
    errors: List[Dict[str, str]]  # employee_id, error_message
    
    class Config:
        from_attributes = True