"""
Simple Training Model - Database Aligned
Minimal model that matches actual database without conflicts
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import BaseModel


class TrainingType(str, enum.Enum):
    """Training types as in database"""
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    CONTINUING_EDUCATION = "continuing_education"


class ProgramStatus(str, enum.Enum):
    """Program status as in database"""
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class TrainingProgramSimple(BaseModel):
    """Simple training program model matching database exactly"""
    __tablename__ = "training_programs"
    __table_args__ = {'extend_existing': True}
    
    # Override BaseModel fields that don't exist in this table
    uuid = None  # This table doesn't have UUID field
    version = Column(Integer, default=1)  # Different from BaseModel version
    is_deleted = None  # This table uses retired_at instead
    
    # Actual database columns (exactly as they exist)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum(TrainingType), nullable=False)
    duration = Column(Integer, nullable=False)
    passing_score = Column(Integer, default=70)
    validity_period = Column(Integer, default=12)
    status = Column(Enum(ProgramStatus), default=ProgramStatus.DRAFT)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    retired_at = Column(DateTime)
    retirement_reason = Column(Text)
    supersedes_id = Column(Integer, ForeignKey("training_programs.id"))
    
    # Simple relationships without conflicts
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<TrainingProgramSimple(id={self.id}, title='{self.title}')>"