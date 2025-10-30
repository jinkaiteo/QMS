"""
Simple Training Schemas - Database Aligned
Pydantic schemas for the simple training model
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TrainingType(str, Enum):
    """Training types"""
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    CONTINUING_EDUCATION = "continuing_education"


class ProgramStatus(str, Enum):
    """Program status"""
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class TrainingProgramBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    type: TrainingType
    duration: int = Field(..., gt=0)
    passing_score: Optional[int] = Field(70, ge=0, le=100)
    validity_period: Optional[int] = Field(12, gt=0)
    department_id: Optional[int] = None


class TrainingProgramCreate(TrainingProgramBase):
    created_by: Optional[int] = None


class TrainingProgramUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    type: Optional[TrainingType] = None
    duration: Optional[int] = Field(None, gt=0)
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    validity_period: Optional[int] = Field(None, gt=0)
    status: Optional[ProgramStatus] = None
    department_id: Optional[int] = None


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