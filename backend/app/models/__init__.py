# QMS Models Package
# Phase 1 & 2: Database models for the QMS system

from app.models.base import BaseModel

# Import models in dependency order to avoid circular imports
from app.models.user import Organization, Department, Role, User, UserRole
from app.models.audit import AuditLog
from app.models.system import SystemSetting

# Phase 2: EDMS Models
from app.models.edms import (
    DocumentType, DocumentCategory, Document, DocumentVersion,
    DocumentWorkflow, WorkflowStep, DigitalSignature,
    DocumentRelationship, DocumentPermission, DocumentComment
)

# Phase 3: QRM Models - Import after User model is defined
from app.models.qrm import (
    QualityEventType, QualityEvent, QualityInvestigation,
    CAPA, CAPAAction, ChangeControlRequest, RiskAssessment
)

# Phase 4: Training Models - Import after User model is defined
try:
    from app.models.training import TrainingRecord
except ImportError:
    # Training models may not be fully implemented yet
    pass

__all__ = [
    "BaseModel",
    "User", 
    "Role", 
    "UserRole", 
    "Organization", 
    "Department",
    "AuditLog",
    "SystemSetting",
    # EDMS Models
    "DocumentType",
    "DocumentCategory", 
    "Document",
    "DocumentVersion",
    "DocumentWorkflow",
    "WorkflowStep",
    "DigitalSignature",
    "DocumentRelationship",
    "DocumentPermission",
    "DocumentComment",
    # QRM Models
    "QualityEventType",
    "QualityEvent",
    "QualityInvestigation",
    "CAPA",
    "CAPAAction",
    "ChangeControlRequest",
    "RiskAssessment"
]
