# QMS Models Package
# Phase 1 & 2: Database models for the QMS system

from app.models.base import BaseModel
from app.models.user import User, Role, UserRole, Organization, Department
from app.models.audit import AuditLog
from app.models.system import SystemSetting

# Phase 2: EDMS Models - Temporarily disabled for testing
# from app.models.edms import (
#     DocumentType, DocumentCategory, Document, DocumentVersion,
#     DocumentWorkflow, WorkflowStep, DigitalSignature,
#     DocumentRelationship, DocumentPermission, DocumentComment
# )

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
    "DocumentComment"
]
