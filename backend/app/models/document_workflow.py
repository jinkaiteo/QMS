"""
Document Workflow Models
Pharmaceutical approval workflow system
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime, timedelta

from app.models.base import BaseModel


class WorkflowStatus(str, enum.Enum):
    """Workflow status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ApprovalAction(str, enum.Enum):
    """Approval action types"""
    APPROVE = "approve"
    REJECT = "reject"
    RETURN_FOR_REVISION = "return_for_revision"
    REQUEST_CHANGES = "request_changes"
    DELEGATE = "delegate"


class SignatureType(str, enum.Enum):
    """Electronic signature types"""
    REVIEW = "review"
    APPROVAL = "approval"
    AUTHOR = "author"
    WITNESS = "witness"


class DocumentWorkflowTemplate(BaseModel):
    """Workflow templates for different document types"""
    __tablename__ = "document_workflow_templates"
    
    # Template information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    document_type_id = Column(Integer, ForeignKey("document_types.id"))
    
    # Workflow configuration
    is_active = Column(Boolean, default=True)
    requires_review = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=True)
    approval_levels = Column(Integer, default=1)
    review_days = Column(Integer, default=5)
    approval_days = Column(Integer, default=3)
    
    # Auto-assignment rules
    auto_assign_reviewers = Column(Boolean, default=False)
    auto_assign_approvers = Column(Boolean, default=False)
    
    # Relationships
    document_type = relationship("DocumentType")
    workflow_steps = relationship("WorkflowStepTemplate", back_populates="template")
    
    def __repr__(self):
        return f"<DocumentWorkflowTemplate(name='{self.name}')>"


class WorkflowStepTemplate(BaseModel):
    """Template for workflow steps"""
    __tablename__ = "workflow_step_templates"
    
    # Step configuration
    template_id = Column(Integer, ForeignKey("document_workflow_templates.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    step_name = Column(String(255), nullable=False)
    step_type = Column(String(50), nullable=False)  # review, approval, notification
    
    # Assignment rules
    role_required = Column(String(100))
    department_id = Column(Integer, ForeignKey("departments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))  # Specific user assignment
    
    # Timing
    days_to_complete = Column(Integer, default=3)
    is_required = Column(Boolean, default=True)
    can_delegate = Column(Boolean, default=True)
    
    # Relationships
    template = relationship("DocumentWorkflowTemplate", back_populates="workflow_steps")
    
    def __repr__(self):
        return f"<WorkflowStepTemplate(step_name='{self.step_name}', order={self.step_order})>"


class DocumentWorkflowInstance(BaseModel):
    """Active workflow instance for a document"""
    __tablename__ = "document_workflow_instances"
    
    # Workflow identification
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("document_workflow_templates.id"))
    workflow_name = Column(String(255), nullable=False)
    
    # Workflow state
    current_step = Column(Integer, default=1)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    
    # Timing
    initiated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    initiated_at = Column(DateTime, default=func.now())
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Workflow metadata
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    comments = Column(Text)
    
    # Relationships
    document = relationship("Document")
    template = relationship("DocumentWorkflowTemplate")
    initiator = relationship("User", foreign_keys=[initiated_by_id])
    workflow_steps = relationship("DocumentWorkflowStep", back_populates="workflow_instance")
    
    def __repr__(self):
        return f"<DocumentWorkflowInstance(document_id={self.document_id}, status='{self.status}')>"


class DocumentWorkflowStep(BaseModel):
    """Individual step in a workflow instance"""
    __tablename__ = "document_workflow_steps"
    
    # Step identification
    workflow_instance_id = Column(Integer, ForeignKey("document_workflow_instances.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    step_name = Column(String(255), nullable=False)
    step_type = Column(String(50), nullable=False)
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    assigned_by_id = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime)
    
    # Completion
    completed_by_id = Column(Integer, ForeignKey("users.id"))
    completed_at = Column(DateTime)
    due_date = Column(DateTime)
    
    # Step state
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    action_taken = Column(Enum(ApprovalAction))
    comments = Column(Text)
    
    # Delegation
    delegated_to_id = Column(Integer, ForeignKey("users.id"))
    delegation_reason = Column(Text)
    
    # Relationships
    workflow_instance = relationship("DocumentWorkflowInstance", back_populates="workflow_steps")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    delegated_to = relationship("User", foreign_keys=[delegated_to_id])
    signatures = relationship("DocumentSignature", back_populates="workflow_step")
    
    def __repr__(self):
        return f"<DocumentWorkflowStep(step_name='{self.step_name}', status='{self.status}')>"


class DocumentSignature(BaseModel):
    """Electronic signatures for document approval"""
    __tablename__ = "document_signatures"
    
    # Signature identification
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    workflow_step_id = Column(Integer, ForeignKey("document_workflow_steps.id"))
    
    # Signer information
    signer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    signature_type = Column(Enum(SignatureType), nullable=False)
    signature_meaning = Column(String(500), nullable=False)
    
    # Signature data
    signature_hash = Column(String(512), nullable=False)
    signature_method = Column(String(100))  # password, certificate, biometric
    ip_address = Column(String(45))
    user_agent = Column(Text)
    location = Column(String(255))
    
    # Timestamp and validation
    signed_at = Column(DateTime, default=func.now())
    is_valid = Column(Boolean, default=True)
    invalidated_at = Column(DateTime)
    invalidation_reason = Column(Text)
    
    # Regulatory compliance
    witnessed_by_id = Column(Integer, ForeignKey("users.id"))
    regulatory_basis = Column(Text)  # 21 CFR Part 11 compliance notes
    
    # Relationships
    document = relationship("Document")
    workflow_step = relationship("DocumentWorkflowStep", back_populates="signatures")
    signer = relationship("User", foreign_keys=[signer_id])
    witness = relationship("User", foreign_keys=[witnessed_by_id])
    
    def __repr__(self):
        return f"<DocumentSignature(signer_id={self.signer_id}, type='{self.signature_type}')>"


class DocumentComment(BaseModel):
    """Comments and feedback on documents"""
    __tablename__ = "document_comments"
    
    # Comment identification
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    workflow_step_id = Column(Integer, ForeignKey("document_workflow_steps.id"))
    parent_comment_id = Column(Integer, ForeignKey("document_comments.id"))
    
    # Comment content
    comment_text = Column(Text, nullable=False)
    comment_type = Column(String(50), default="general")  # general, suggestion, issue, question
    
    # Location context
    page_number = Column(Integer)
    section_reference = Column(String(255))
    line_number = Column(Integer)
    
    # Comment metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_resolved = Column(Boolean, default=False)
    resolved_by_id = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    resolution_comment = Column(Text)
    
    # Visibility and priority
    is_private = Column(Boolean, default=False)
    priority = Column(String(20), default="normal")
    
    # Relationships
    document = relationship("Document")
    workflow_step = relationship("DocumentWorkflowStep")
    parent_comment = relationship("DocumentComment", remote_side="DocumentComment.id")
    replies = relationship("DocumentComment", back_populates="parent_comment")
    created_by = relationship("User", foreign_keys=[created_by_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    
    def __repr__(self):
        return f"<DocumentComment(document_id={self.document_id}, type='{self.comment_type}')>"


class DocumentNotification(BaseModel):
    """Notification system for workflow events"""
    __tablename__ = "document_notifications"
    
    # Notification identification
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    workflow_instance_id = Column(Integer, ForeignKey("document_workflow_instances.id"))
    
    # Recipient
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # assignment, reminder, completion, etc.
    
    # Notification content
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    
    # Delivery
    sent_at = Column(DateTime)
    read_at = Column(DateTime)
    is_read = Column(Boolean, default=False)
    delivery_method = Column(String(50), default="email")  # email, in_app, sms
    
    # Action
    action_required = Column(Boolean, default=False)
    action_url = Column(String(500))
    action_deadline = Column(DateTime)
    
    # Relationships
    document = relationship("Document")
    workflow_instance = relationship("DocumentWorkflowInstance")
    recipient = relationship("User")
    
    def __repr__(self):
        return f"<DocumentNotification(recipient_id={self.recipient_id}, type='{self.notification_type}')>"