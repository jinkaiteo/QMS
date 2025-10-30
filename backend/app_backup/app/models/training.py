"""
Training Management System (TRM) Models
Phase 4 Implementation - QMS Platform v3.0

Core models for training programs, sessions, employee records, 
competencies, and compliance tracking.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    Numeric, ForeignKey, Enum, JSON, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import BaseModel


class TrainingType(str, enum.Enum):
    """Types of training programs"""
    ONBOARDING = "onboarding"
    COMPLIANCE = "compliance"
    TECHNICAL = "technical"
    SAFETY = "safety"
    LEADERSHIP = "leadership"
    CONTINUING_EDUCATION = "continuing_education"


class TrainingStatus(str, enum.Enum):
    """Training completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    EXPIRED = "expired"
    OVERDUE = "overdue"


class DeliveryMethod(str, enum.Enum):
    """Training delivery methods"""
    ONLINE = "online"
    CLASSROOM = "classroom"
    HANDS_ON = "hands_on"
    SELF_PACED = "self_paced"
    BLENDED = "blended"


class CompetencyLevel(str, enum.Enum):
    """Competency proficiency levels"""
    NOVICE = "novice"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class TrainingProgram(BaseModel):
    """Training program/course definitions"""
    __tablename__ = "training_programs"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    training_type = Column(Enum(TrainingType), nullable=False)
    delivery_method = Column(Enum(DeliveryMethod), nullable=False)
    duration_hours = Column(Numeric(5, 2))
    validity_months = Column(Integer)  # How long certification is valid
    
    # Content and requirements
    learning_objectives = Column(JSON)  # List of learning objectives
    prerequisites = Column(JSON)  # Required prior training/skills
    materials_required = Column(JSON)  # Equipment, documents needed
    
    # Compliance and approval
    regulatory_requirement = Column(Boolean, default=False)
    approval_required = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    effective_date = Column(DateTime, default=func.now())
    retirement_date = Column(DateTime)
    
    # Relationships
    sessions = relationship("TrainingSession", back_populates="program")
    employee_records = relationship("EmployeeTraining", back_populates="program")
    competency_mappings = relationship("CompetencyMapping", back_populates="program")
    
    def __repr__(self):
        return f"<TrainingProgram {self.code}: {self.title}>"


class TrainingSession(BaseModel):
    """Scheduled training sessions/events"""
    __tablename__ = "training_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    session_code = Column(String(50), unique=True, nullable=False)
    
    # Schedule details
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    location = Column(String(200))  # Room, online platform, etc.
    max_participants = Column(Integer)
    min_participants = Column(Integer)
    
    # Instructor information
    instructor_id = Column(Integer, ForeignKey("users.id"))
    instructor_notes = Column(Text)
    
    # Session status
    status = Column(String(20), default="scheduled")  # scheduled, in_progress, completed, cancelled
    completion_notes = Column(Text)
    
    # Relationships
    program = relationship("TrainingProgram", back_populates="sessions")
    instructor = relationship("User", foreign_keys=[instructor_id])
    attendees = relationship("SessionAttendance", back_populates="session")
    
    def __repr__(self):
        return f"<TrainingSession {self.session_code}: {self.program.title}>"


class EmployeeTraining(BaseModel):
    """Individual employee training records"""
    __tablename__ = "employee_training"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    
    # Training assignment
    assigned_date = Column(DateTime, default=func.now())
    due_date = Column(DateTime)
    assigned_by_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(String(500))  # Why this training was assigned
    
    # Training completion
    status = Column(Enum(TrainingStatus), default=TrainingStatus.NOT_STARTED)
    start_date = Column(DateTime)
    completion_date = Column(DateTime)
    score = Column(Numeric(5, 2))  # Assessment score if applicable
    pass_fail = Column(Boolean)
    
    # Certification
    certificate_issued = Column(Boolean, default=False)
    certificate_number = Column(String(100))
    certification_date = Column(DateTime)
    expiry_date = Column(DateTime)
    
    # Notes and feedback
    employee_feedback = Column(Text)
    supervisor_notes = Column(Text)
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    program = relationship("TrainingProgram", back_populates="employee_records")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    assessments = relationship("TrainingAssessment", back_populates="employee_training")
    
    def __repr__(self):
        return f"<EmployeeTraining {self.employee.username}: {self.program.title}>"


class SessionAttendance(BaseModel):
    """Track attendance at training sessions"""
    __tablename__ = "session_attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee_training_id = Column(Integer, ForeignKey("employee_training.id"))
    
    # Attendance tracking
    registered_date = Column(DateTime, default=func.now())
    attended = Column(Boolean)
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    attendance_notes = Column(Text)
    
    # Relationships
    session = relationship("TrainingSession", back_populates="attendees")
    employee = relationship("User")
    employee_training = relationship("EmployeeTraining")
    
    def __repr__(self):
        return f"<SessionAttendance {self.employee.username}: {self.session.session_code}>"


class Competency(BaseModel):
    """Core competencies and skills"""
    __tablename__ = "competencies"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # Technical, Behavioral, Leadership, etc.
    
    # Relationships
    role_mappings = relationship("RoleCompetency", back_populates="competency")
    training_mappings = relationship("CompetencyMapping", back_populates="competency")
    assessments = relationship("CompetencyAssessment", back_populates="competency")
    
    def __repr__(self):
        return f"<Competency {self.code}: {self.name}>"


class RoleCompetency(BaseModel):
    """Required competencies for job roles"""
    __tablename__ = "role_competencies"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    required_level = Column(Enum(CompetencyLevel), nullable=False)
    critical = Column(Boolean, default=False)  # Is this a critical competency?
    
    # Relationships
    role = relationship("Role")
    competency = relationship("Competency", back_populates="role_mappings")
    
    def __repr__(self):
        return f"<RoleCompetency {self.role.name}: {self.competency.name}>"


class CompetencyMapping(BaseModel):
    """Map training programs to competencies they develop"""
    __tablename__ = "competency_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    competency_level = Column(Enum(CompetencyLevel), nullable=False)
    
    # Relationships
    program = relationship("TrainingProgram", back_populates="competency_mappings")
    competency = relationship("Competency", back_populates="training_mappings")
    
    def __repr__(self):
        return f"<CompetencyMapping {self.program.title}: {self.competency.name}>"


class CompetencyAssessment(BaseModel):
    """Individual competency assessments"""
    __tablename__ = "competency_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    assessor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Assessment details
    assessment_date = Column(Date, nullable=False)
    current_level = Column(Enum(CompetencyLevel), nullable=False)
    target_level = Column(Enum(CompetencyLevel))
    assessment_method = Column(String(100))  # Observation, test, project, etc.
    
    # Results and recommendations
    strengths = Column(Text)
    improvement_areas = Column(Text)
    recommended_training = Column(JSON)  # List of recommended training programs
    next_assessment_date = Column(Date)
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    competency = relationship("Competency", back_populates="assessments")
    assessor = relationship("User", foreign_keys=[assessor_id])
    
    def __repr__(self):
        return f"<CompetencyAssessment {self.employee.username}: {self.competency.name}>"


class TrainingAssessment(BaseModel):
    """Training program assessments and evaluations"""
    __tablename__ = "training_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_training_id = Column(Integer, ForeignKey("employee_training.id"), nullable=False)
    assessment_type = Column(String(50))  # quiz, exam, practical, evaluation
    
    # Assessment details
    assessment_date = Column(DateTime, default=func.now())
    max_score = Column(Numeric(5, 2))
    achieved_score = Column(Numeric(5, 2))
    pass_threshold = Column(Numeric(5, 2))
    passed = Column(Boolean)
    
    # Content
    questions = Column(JSON)  # Assessment questions and answers
    feedback = Column(Text)
    improvement_recommendations = Column(Text)
    
    # Relationships
    employee_training = relationship("EmployeeTraining", back_populates="assessments")
    
    def __repr__(self):
        return f"<TrainingAssessment {self.employee_training.employee.username}: {self.assessment_type}>"