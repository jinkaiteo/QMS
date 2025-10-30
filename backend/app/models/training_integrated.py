"""
Training Management System (TRM) Models - Database Integrated
Corrected models that match the actual database schema
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import BaseModel
from app.models.user import User
from app.models.user import Department, Role


# Database enums (must match database exactly)
class TrainingType(str, enum.Enum):
    """Training types as defined in database"""
    MANDATORY = "mandatory"
    OPTIONAL = "optional" 
    CONTINUING_EDUCATION = "continuing_education"


class ProgramStatus(str, enum.Enum):
    """Program status as defined in database"""
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class AssignmentStatus(str, enum.Enum):
    """Assignment status as defined in database"""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    EXPIRED = "expired"


class TrainingProgram(BaseModel):
    """Training program model matching actual database schema"""
    __tablename__ = "training_programs"
    __table_args__ = {'extend_existing': True}
    
    # Override BaseModel fields that don't exist in this table
    uuid = None  # This table doesn't have UUID field
    version = Column(Integer, default=1)  # Different from BaseModel
    is_deleted = None  # This table uses retired_at instead
    
    # Actual database columns
    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum(TrainingType), nullable=False)  # Note: 'type' not 'training_type'
    duration = Column(Integer, nullable=False)  # Note: 'duration' not 'duration_hours'
    passing_score = Column(Integer, default=70)
    validity_period = Column(Integer, default=12)  # Note: 'validity_period' not 'validity_months'
    status = Column(Enum(ProgramStatus), default=ProgramStatus.DRAFT)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    retired_at = Column(DateTime)
    retirement_reason = Column(Text)
    supersedes_id = Column(Integer, ForeignKey("training_programs.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    department = relationship("Department")
    superseded_program = relationship("TrainingProgram", remote_side="TrainingProgram.id")
    
    # Training system relationships
    assignments = relationship("TrainingAssignment", back_populates="program")
    modules = relationship("TrainingModule", back_populates="program")
    documents = relationship("TrainingDocument", back_populates="program")
    prerequisites = relationship("TrainingPrerequisite", foreign_keys="TrainingPrerequisite.program_id", back_populates="program")
    
    def __repr__(self):
        return f"<TrainingProgram(id={self.id}, title='{self.title}')>"


class TrainingAssignment(BaseModel):
    """Training assignments to employees"""
    __tablename__ = "training_assignments"
    
    # Override BaseModel fields that don't exist
    uuid = None
    version = None
    is_deleted = None
    
    # Actual database columns
    program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"))
    assigned_date = Column(DateTime, default=func.now())
    due_date = Column(DateTime)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.ASSIGNED)
    started_date = Column(DateTime)
    completed_date = Column(DateTime)
    score = Column(Integer)
    passed = Column(Boolean)
    certificate_issued = Column(Boolean, default=False)
    expiry_date = Column(DateTime)
    notes = Column(Text)
    
    # Relationships
    program = relationship("TrainingProgram", back_populates="assignments")
    employee = relationship("User", foreign_keys=[employee_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    
    def __repr__(self):
        return f"<TrainingAssignment(program_id={self.program_id}, employee_id={self.employee_id})>"


class TrainingModule(BaseModel):
    """Training modules within programs"""
    __tablename__ = "training_modules"
    
    # Override BaseModel fields
    uuid = None
    version = None
    is_deleted = None
    
    # Actual database columns
    program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    module_order = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(Text)
    duration_minutes = Column(Integer)
    is_required = Column(Boolean, default=True)
    passing_score = Column(Integer)
    
    # Relationships
    program = relationship("TrainingProgram", back_populates="modules")
    
    def __repr__(self):
        return f"<TrainingModule(program_id={self.program_id}, title='{self.title}')>"


class TrainingDocument(BaseModel):
    """Documents associated with training programs"""
    __tablename__ = "training_documents"
    
    # Override BaseModel fields
    uuid = None
    version = None
    is_deleted = None
    
    # Actual database columns
    program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    document_type = Column(String(50))  # manual, presentation, assessment, etc.
    is_required = Column(Boolean, default=False)
    
    # Relationships
    program = relationship("TrainingProgram", back_populates="documents")
    
    def __repr__(self):
        return f"<TrainingDocument(program_id={self.program_id}, title='{self.title}')>"


class TrainingPrerequisite(BaseModel):
    """Prerequisites between training programs"""
    __tablename__ = "training_prerequisites"
    
    # Override BaseModel fields
    uuid = None
    version = None
    is_deleted = None
    
    # Actual database columns
    program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    prerequisite_program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    is_required = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relationships
    program = relationship("TrainingProgram", foreign_keys=[program_id], back_populates="prerequisites")
    prerequisite_program = relationship("TrainingProgram", foreign_keys=[prerequisite_program_id])
    
    def __repr__(self):
        return f"<TrainingPrerequisite(program_id={self.program_id}, prerequisite_id={self.prerequisite_program_id})>"


# Summary table for dashboard/reporting
class EmployeeTrainingSummary(BaseModel):
    """Employee training summary for dashboard"""
    __tablename__ = "employee_training_summary"
    
    # Override BaseModel fields
    uuid = None
    version = None
    is_deleted = None
    
    # Actual database columns
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_assigned = Column(Integer, default=0)
    total_completed = Column(Integer, default=0)
    total_overdue = Column(Integer, default=0)
    total_expired = Column(Integer, default=0)
    compliance_percentage = Column(Integer, default=0)
    last_updated = Column(DateTime, default=func.now())
    
    # Relationships
    employee = relationship("User")
    
    def __repr__(self):
        return f"<EmployeeTrainingSummary(employee_id={self.employee_id}, compliance={self.compliance_percentage}%)>"


class TrainingDashboardStats(BaseModel):
    """Training dashboard statistics"""
    __tablename__ = "training_dashboard_stats"
    
    # Override BaseModel fields
    uuid = None
    version = None
    is_deleted = None
    
    # Actual database columns
    total_programs = Column(Integer, default=0)
    active_programs = Column(Integer, default=0)
    total_assignments = Column(Integer, default=0)
    completed_assignments = Column(Integer, default=0)
    overdue_assignments = Column(Integer, default=0)
    overall_compliance_rate = Column(Integer, default=0)
    last_calculated = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<TrainingDashboardStats(programs={self.total_programs}, compliance={self.overall_compliance_rate}%)>"