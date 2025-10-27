# QRM Models - Phase 3
# Quality Risk Management models

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Float,
    ForeignKey, Table, ARRAY, BigInteger, LargeBinary, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from typing import List, Optional
from datetime import datetime, date

from app.models.base import BaseModel


class QualityEventType(BaseModel):
    __tablename__ = "quality_event_types"

    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    severity_levels = Column(ARRAY(String), default=[])
    color = Column(String(7), comment="Hex color code for UI")
    icon = Column(String(50), comment="Icon identifier")

    # Relationships
    quality_events = relationship("QualityEvent", back_populates="event_type")


class QualityEvent(BaseModel):
    __tablename__ = "quality_events"

    event_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    event_type_id = Column(Integer, ForeignKey("quality_event_types.id"), nullable=False)
    severity = Column(String(50), nullable=False)
    priority = Column(Integer, default=3)
    source = Column(String(100))
    
    # Event details
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    discovered_at = Column(DateTime(timezone=True), default=func.now())
    location = Column(String(255))
    department_id = Column(Integer, ForeignKey("departments.id"))
    
    # People involved
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    investigator_id = Column(Integer, ForeignKey("users.id"))
    
    # Product/Process impact
    product_affected = Column(String(255))
    batch_lot_numbers = Column(ARRAY(String), default=[])
    processes_affected = Column(ARRAY(String), default=[])
    
    # Impact assessment
    patient_safety_impact = Column(Boolean, default=False)
    product_quality_impact = Column(Boolean, default=False)
    regulatory_impact = Column(Boolean, default=False)
    business_impact_severity = Column(String(50))
    estimated_cost = Column(DECIMAL(12, 2))
    
    # Status and workflow
    status = Column(String(50), default="open")
    investigation_required = Column(Boolean, default=True)
    capa_required = Column(Boolean, default=False)
    regulatory_reporting_required = Column(Boolean, default=False)
    
    # Dates and deadlines
    investigation_due_date = Column(Date)
    capa_due_date = Column(Date)
    regulatory_due_date = Column(Date)
    target_closure_date = Column(Date)
    actual_closure_date = Column(Date)
    
    # Resolution
    root_cause = Column(Text)
    immediate_actions = Column(Text)
    containment_actions = Column(Text)
    
    # Compliance
    gmp_classification = Column(String(50))
    regulatory_citations = Column(ARRAY(String), default=[])
    
    # Relationships
    parent_event_id = Column(Integer, ForeignKey("quality_events.id"))
    related_documents = Column(ARRAY(Integer), default=[], comment="Array of document IDs")
    
    # Relationships
    event_type = relationship("QualityEventType", back_populates="quality_events")
    department = relationship("Department", foreign_keys=[department_id])
    reporter = relationship("User", foreign_keys=[reporter_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    investigator = relationship("User", foreign_keys=[investigator_id])
    
    # Self-referential relationship
    parent_event = relationship("QualityEvent", remote_side="QualityEvent.id")
    child_events = relationship("QualityEvent", back_populates="parent_event")
    
    # Child relationships
    investigations = relationship("QualityInvestigation", back_populates="quality_event")
    capas = relationship("CAPA", back_populates="quality_event")


class QualityInvestigation(BaseModel):
    __tablename__ = "quality_investigations"

    quality_event_id = Column(Integer, ForeignKey("quality_events.id"), nullable=False)
    investigation_number = Column(String(100), unique=True, nullable=False)
    
    # Investigation team
    lead_investigator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_members = Column(ARRAY(Integer), default=[], comment="Array of user IDs")
    
    # Investigation details
    methodology = Column(String(100))
    scope_definition = Column(Text)
    timeline_of_events = Column(Text)
    evidence_collected = Column(Text)
    interviews_conducted = Column(Text)
    
    # Root cause analysis
    immediate_cause = Column(Text)
    root_cause = Column(Text)
    contributing_factors = Column(Text)
    
    # Risk assessment
    risk_level = Column(String(50))
    risk_score = Column(Integer)
    likelihood = Column(String(50))
    severity_impact = Column(String(50))
    
    # Investigation status
    status = Column(String(50), default="planning")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Documentation
    investigation_report_path = Column(String(500))
    evidence_documents = Column(ARRAY(Integer), default=[], comment="Array of document IDs")
    
    # Approval
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Relationships
    quality_event = relationship("QualityEvent", back_populates="investigations")
    lead_investigator = relationship("User", foreign_keys=[lead_investigator_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    approver = relationship("User", foreign_keys=[approved_by])


class CAPA(BaseModel):
    __tablename__ = "capas"

    capa_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # CAPA classification
    capa_type = Column(String(50), nullable=False)
    action_category = Column(String(100))
    
    # Source and relationships
    source_type = Column(String(100))
    source_id = Column(Integer)
    quality_event_id = Column(Integer, ForeignKey("quality_events.id"))
    investigation_id = Column(Integer, ForeignKey("quality_investigations.id"))
    
    # Assignment and responsibility
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    responsible_department_id = Column(Integer, ForeignKey("departments.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"))
    
    # CAPA details
    problem_statement = Column(Text, nullable=False)
    root_cause = Column(Text)
    proposed_solution = Column(Text, nullable=False)
    implementation_plan = Column(Text)
    success_criteria = Column(Text)
    
    # Timeline
    target_start_date = Column(Date)
    target_completion_date = Column(Date, nullable=False)
    actual_start_date = Column(Date)
    actual_completion_date = Column(Date)
    
    # Resources
    estimated_cost = Column(DECIMAL(12, 2))
    actual_cost = Column(DECIMAL(12, 2))
    resources_required = Column(Text)
    
    # Priority and risk
    priority = Column(Integer, default=3)
    risk_level = Column(String(50))
    
    # Status tracking
    status = Column(String(50), default="planning")
    completion_percentage = Column(Integer, default=0)
    
    # Effectiveness verification
    verification_method = Column(Text)
    verification_criteria = Column(Text)
    verification_due_date = Column(Date)
    verification_completed_date = Column(Date)
    effectiveness_confirmed = Column(Boolean, default=False)
    verification_comments = Column(Text)
    
    # Approval workflow
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Related documents and training
    related_documents = Column(ARRAY(Integer), default=[], comment="Array of document IDs")
    training_required = Column(Boolean, default=False)
    training_plan_id = Column(Integer)
    
    # Relationships
    quality_event = relationship("QualityEvent", back_populates="capas")
    investigation = relationship("QualityInvestigation", foreign_keys=[investigation_id])
    owner = relationship("User", foreign_keys=[owner_id])
    responsible_department = relationship("Department", foreign_keys=[responsible_department_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    # Child relationships
    actions = relationship("CAPAAction", back_populates="capa")


class CAPAAction(BaseModel):
    __tablename__ = "capa_actions"

    capa_id = Column(Integer, ForeignKey("capas.id"), nullable=False)
    action_number = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    
    # Timeline
    due_date = Column(Date, nullable=False)
    completed_date = Column(Date)
    
    # Status
    status = Column(String(50), default="open")
    completion_percentage = Column(Integer, default=0)
    
    # Dependencies
    depends_on = Column(ARRAY(Integer), default=[], comment="Array of other action IDs")
    
    # Evidence and verification
    completion_evidence = Column(Text)
    verification_required = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"))
    verified_at = Column(DateTime(timezone=True))
    
    # Relationships
    capa = relationship("CAPA", back_populates="actions")
    assignee = relationship("User", foreign_keys=[assigned_to])
    department = relationship("Department", foreign_keys=[department_id])
    verifier = relationship("User", foreign_keys=[verified_by])

    __table_args__ = (
        {"comment": "Individual action items within CAPAs"},
    )


class ChangeControlRequest(BaseModel):
    __tablename__ = "change_control_requests"

    change_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Change classification
    change_type = Column(String(50), nullable=False)
    change_category = Column(String(100))
    urgency = Column(String(50))
    
    # Initiator and assignment
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    change_owner_id = Column(Integer, ForeignKey("users.id"))
    affected_departments = Column(ARRAY(Integer), default=[], comment="Array of department IDs")
    
    # Change details
    current_state = Column(Text, nullable=False)
    proposed_state = Column(Text, nullable=False)
    justification = Column(Text, nullable=False)
    benefits = Column(Text)
    
    # Impact assessment
    validation_impact = Column(Boolean, default=False)
    gmp_impact = Column(Boolean, default=False)
    regulatory_impact = Column(Boolean, default=False)
    safety_impact = Column(Boolean, default=False)
    environmental_impact = Column(Boolean, default=False)
    
    # Risk assessment
    risk_assessment = Column(Text)
    risk_level = Column(String(50))
    mitigation_measures = Column(Text)
    
    # Implementation
    implementation_plan = Column(Text)
    rollback_plan = Column(Text)
    testing_requirements = Column(Text)
    training_requirements = Column(Text)
    documentation_updates = Column(Text)
    
    # Timeline
    requested_date = Column(Date, nullable=False)
    target_implementation_date = Column(Date)
    actual_implementation_date = Column(Date)
    
    # Resources
    estimated_cost = Column(DECIMAL(12, 2))
    actual_cost = Column(DECIMAL(12, 2))
    resources_required = Column(Text)
    
    # Status and approval
    status = Column(String(50), default="submitted")
    priority = Column(Integer, default=3)
    
    # Approval workflow
    technical_reviewer_id = Column(Integer, ForeignKey("users.id"))
    technical_review_date = Column(Date)
    technical_review_comments = Column(Text)
    
    quality_reviewer_id = Column(Integer, ForeignKey("users.id"))
    quality_review_date = Column(Date)
    quality_review_comments = Column(Text)
    
    final_approver_id = Column(Integer, ForeignKey("users.id"))
    final_approval_date = Column(Date)
    final_approval_comments = Column(Text)
    
    # Implementation tracking
    implementation_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"))
    verification_date = Column(Date)
    verification_comments = Column(Text)
    
    # Post-implementation
    effectiveness_review_due_date = Column(Date)
    effectiveness_confirmed = Column(Boolean, default=False)
    effectiveness_comments = Column(Text)
    
    # Related records
    related_quality_events = Column(ARRAY(Integer), default=[], comment="Array of quality event IDs")
    related_capas = Column(ARRAY(Integer), default=[], comment="Array of CAPA IDs")
    related_documents = Column(ARRAY(Integer), default=[], comment="Array of document IDs")
    
    # Relationships
    initiator = relationship("User", foreign_keys=[initiator_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    change_owner = relationship("User", foreign_keys=[change_owner_id])
    technical_reviewer = relationship("User", foreign_keys=[technical_reviewer_id])
    quality_reviewer = relationship("User", foreign_keys=[quality_reviewer_id])
    final_approver = relationship("User", foreign_keys=[final_approver_id])
    verifier = relationship("User", foreign_keys=[verified_by])


class RiskAssessment(BaseModel):
    __tablename__ = "risk_assessments"

    assessment_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Assessment type and scope
    assessment_type = Column(String(100))
    methodology = Column(String(100))
    scope_definition = Column(Text, nullable=False)
    
    # Assessment team
    lead_assessor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_members = Column(ARRAY(Integer), default=[], comment="Array of user IDs")
    
    # Risk criteria
    risk_matrix = Column(JSONB, comment="Risk matrix configuration")
    likelihood_scale = Column(JSONB, comment="Likelihood scale definition")
    severity_scale = Column(JSONB, comment="Severity scale definition")
    
    # Assessment results
    identified_risks = Column(JSONB, comment="Array of identified risks")
    risk_scores = Column(JSONB, comment="Risk scoring results")
    control_measures = Column(JSONB, comment="Existing control measures")
    residual_risks = Column(JSONB, comment="Risks after controls")
    
    # Overall assessment
    overall_risk_level = Column(String(50))
    acceptability = Column(String(50))
    
    # Action items
    recommended_actions = Column(Text)
    action_plan = Column(Text)
    
    # Status and approval
    status = Column(String(50), default="planning")
    completed_date = Column(Date)
    
    # Review and approval
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    review_date = Column(Date)
    review_comments = Column(Text)
    
    approved_by = Column(Integer, ForeignKey("users.id"))
    approval_date = Column(Date)
    approval_comments = Column(Text)
    
    # Periodic review
    review_frequency_months = Column(Integer, default=12)
    next_review_due_date = Column(Date)
    
    # Related records
    related_processes = Column(ARRAY(String), default=[])
    related_products = Column(ARRAY(String), default=[])
    related_documents = Column(ARRAY(Integer), default=[], comment="Array of document IDs")
    
    # Relationships
    lead_assessor = relationship("User", foreign_keys=[lead_assessor_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    approver = relationship("User", foreign_keys=[approved_by])


# Update User model relationships (to be added to user.py)
"""
Add these relationships to the User model:

    # QRM relationships (Phase 3)
    reported_quality_events = relationship("QualityEvent", foreign_keys="QualityEvent.reporter_id", back_populates="reporter")
    assigned_quality_events = relationship("QualityEvent", foreign_keys="QualityEvent.assigned_to", back_populates="assignee")
    investigated_quality_events = relationship("QualityEvent", foreign_keys="QualityEvent.investigator_id", back_populates="investigator")
    
    owned_capas = relationship("CAPA", foreign_keys="CAPA.owner_id", back_populates="owner")
    assigned_capas = relationship("CAPA", foreign_keys="CAPA.assigned_to", back_populates="assignee")
    assigned_capa_actions = relationship("CAPAAction", foreign_keys="CAPAAction.assigned_to", back_populates="assignee")
    
    initiated_change_requests = relationship("ChangeControlRequest", foreign_keys="ChangeControlRequest.initiator_id", back_populates="initiator")
    led_risk_assessments = relationship("RiskAssessment", foreign_keys="RiskAssessment.lead_assessor_id", back_populates="lead_assessor")
"""