"""
Training Management System (TRM) Schemas - Database Integrated
Pydantic schemas that match the actual database structure
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

# Import the actual enum types
from app.models.training_integrated import TrainingType, ProgramStatus, AssignmentStatus


# Base schemas
class TrainingProgramBase(BaseModel):
    title: str = Field(..., max_length=255, description="Program title")
    description: Optional[str] = Field(None, description="Program description")
    type: TrainingType = Field(..., description="Training type")
    duration: int = Field(..., gt=0, description="Duration in hours")
    passing_score: Optional[int] = Field(70, ge=0, le=100, description="Passing score percentage")
    validity_period: Optional[int] = Field(12, gt=0, description="Validity period in months")
    department_id: Optional[int] = Field(None, description="Department ID")


class TrainingProgramCreate(TrainingProgramBase):
    created_by: Optional[int] = Field(None, description="Creator user ID")


class TrainingProgramUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    type: Optional[TrainingType] = None
    duration: Optional[int] = Field(None, gt=0)
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    validity_period: Optional[int] = Field(None, gt=0)
    status: Optional[ProgramStatus] = None
    department_id: Optional[int] = None
    retirement_reason: Optional[str] = None


class TrainingProgramResponse(TrainingProgramBase):
    id: int
    status: ProgramStatus
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    retired_at: Optional[datetime]
    retirement_reason: Optional[str]
    version: int
    supersedes_id: Optional[int]
    
    class Config:
        from_attributes = True


# Training Assignment schemas
class TrainingAssignmentBase(BaseModel):
    program_id: int = Field(..., description="Training program ID")
    employee_id: int = Field(..., description="Employee user ID")
    due_date: Optional[datetime] = Field(None, description="Assignment due date")
    notes: Optional[str] = Field(None, description="Assignment notes")


class TrainingAssignmentCreate(TrainingAssignmentBase):
    assigned_by_id: Optional[int] = Field(None, description="Assigner user ID")


class TrainingAssignmentUpdate(BaseModel):
    due_date: Optional[datetime] = None
    status: Optional[AssignmentStatus] = None
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    passed: Optional[bool] = None
    notes: Optional[str] = None


class TrainingAssignmentResponse(TrainingAssignmentBase):
    id: int
    assigned_by_id: Optional[int]
    assigned_date: datetime
    status: AssignmentStatus
    started_date: Optional[datetime]
    completed_date: Optional[datetime]
    score: Optional[int]
    passed: Optional[bool]
    certificate_issued: bool
    expiry_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Training Module schemas
class TrainingModuleBase(BaseModel):
    program_id: int = Field(..., description="Training program ID")
    module_order: int = Field(..., ge=1, description="Module order")
    title: str = Field(..., max_length=255, description="Module title")
    description: Optional[str] = Field(None, description="Module description")
    content: Optional[str] = Field(None, description="Module content")
    duration_minutes: Optional[int] = Field(None, gt=0, description="Duration in minutes")
    is_required: bool = Field(True, description="Is module required")
    passing_score: Optional[int] = Field(None, ge=0, le=100, description="Module passing score")


class TrainingModuleCreate(TrainingModuleBase):
    pass


class TrainingModuleUpdate(BaseModel):
    module_order: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    is_required: Optional[bool] = None
    passing_score: Optional[int] = Field(None, ge=0, le=100)


class TrainingModuleResponse(TrainingModuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Dashboard and summary schemas
class EmployeeTrainingSummaryResponse(BaseModel):
    employee_id: int
    total_assigned: int
    total_completed: int
    total_overdue: int
    total_expired: int
    compliance_percentage: int
    last_updated: datetime
    
    class Config:
        from_attributes = True


class TrainingDashboardResponse(BaseModel):
    total_programs: int
    active_programs: int
    total_assignments: int
    completed_assignments: int
    overdue_assignments: int
    overall_compliance_rate: int
    last_calculated: datetime
    
    class Config:
        from_attributes = True


# Bulk operations
class BulkAssignmentRequest(BaseModel):
    program_id: int = Field(..., description="Training program ID")
    employee_ids: List[int] = Field(..., min_items=1, description="List of employee IDs")
    due_date: Optional[datetime] = Field(None, description="Assignment due date")
    notes: Optional[str] = Field(None, description="Assignment notes")


class BulkAssignmentResponse(BaseModel):
    successful_assignments: int
    failed_assignments: int
    assignment_ids: List[int]
    errors: List[Dict[str, Any]]


# Search and filter schemas
class TrainingProgramFilter(BaseModel):
    type: Optional[TrainingType] = None
    status: Optional[ProgramStatus] = None
    department_id: Optional[int] = None
    created_by: Optional[int] = None
    search: Optional[str] = Field(None, description="Search in title and description")


class TrainingAssignmentFilter(BaseModel):
    program_id: Optional[int] = None
    employee_id: Optional[int] = None
    status: Optional[AssignmentStatus] = None
    assigned_by_id: Optional[int] = None
    overdue_only: bool = Field(False, description="Show only overdue assignments")
    expiring_soon: bool = Field(False, description="Show assignments expiring within 30 days")


# Response wrappers for lists
class TrainingProgramListResponse(BaseModel):
    items: List[TrainingProgramResponse]
    total: int
    page: int
    per_page: int
    pages: int


class TrainingAssignmentListResponse(BaseModel):
    items: List[TrainingAssignmentResponse]
    total: int
    page: int
    per_page: int
    pages: int