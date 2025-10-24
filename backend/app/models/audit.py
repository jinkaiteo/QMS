# QMS Audit Models
# Phase 1: Audit trail models for 21 CFR Part 11 compliance

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, INET, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import BaseModel


class AuditAction(enum.Enum):
    """Audit action enumeration for tracking operations"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    SIGN = "SIGN"
    DOWNLOAD = "DOWNLOAD"


# Create PostgreSQL ENUM type
audit_action_enum = ENUM(AuditAction, name="audit_action", create_type=False)


class AuditLog(BaseModel):
    """
    Comprehensive audit log model for 21 CFR Part 11 compliance
    Tracks all system activities for regulatory requirements
    """
    
    __tablename__ = "audit_logs"
    
    # Override ID to use BigInteger for large audit volumes
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Timestamp (immutable, set by database)
    timestamp = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False, 
        comment="Audit event timestamp (UTC)"
    )
    
    # User Information
    user_id = Column(Integer, ForeignKey("users.id"), comment="User who performed the action")
    username = Column(String(100), nullable=False, comment="Username at time of action")
    
    # Action Details
    action = Column(audit_action_enum, nullable=False, comment="Type of action performed")
    table_name = Column(String(100), nullable=False, comment="Database table affected")
    record_id = Column(String(100), comment="ID of the affected record")
    
    # Data Changes (for UPDATE operations)
    old_values = Column(JSONB, comment="Previous values before change")
    new_values = Column(JSONB, comment="New values after change")
    
    # Session Information
    ip_address = Column(INET, comment="Client IP address")
    user_agent = Column(Text, comment="Client user agent string")
    session_id = Column(String(100), comment="Session identifier")
    
    # Context Information
    module = Column(String(50), comment="QMS module (EDMS, QRM, TRM, LIMS, SYSTEM)")
    reason = Column(Text, comment="Reason for the action (if provided)")
    
    # Data Integrity
    data_hash = Column(String(128), comment="SHA-256 hash for data integrity verification")
    
    # System vs User Action
    is_system_action = Column(Boolean, default=False, comment="True if action was performed by system")
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.username})>"
    
    @property
    def is_data_change(self):
        """Check if this audit entry represents a data change"""
        return self.action in [AuditAction.CREATE, AuditAction.UPDATE, AuditAction.DELETE]
    
    def verify_integrity(self):
        """Verify the integrity of the audit log entry using data hash"""
        if not self.data_hash:
            return False
        
        from app.core.security import SecurityUtils
        
        # Reconstruct the data for hash calculation
        data_for_hash = {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "action": self.action.value if self.action else None,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "old_values": self.old_values,
            "new_values": self.new_values
        }
        
        calculated_hash = SecurityUtils.calculate_hash(str(data_for_hash))
        return calculated_hash == self.data_hash


class SystemEvent(BaseModel):
    """System events model for tracking application events"""
    
    __tablename__ = "system_events"
    
    event_type = Column(String(100), nullable=False, comment="Type of system event")
    event_category = Column(String(50), nullable=False, comment="Event category (startup, shutdown, error, etc.)")
    severity = Column(String(20), default="INFO", comment="Event severity level")
    description = Column(Text, nullable=False, comment="Event description")
    details = Column(JSONB, comment="Additional event details")
    
    # System Information
    hostname = Column(String(255), comment="Hostname where event occurred")
    application_version = Column(String(50), comment="Application version")
    
    # Error Information (if applicable)
    error_code = Column(String(50), comment="Error code if event is an error")
    stack_trace = Column(Text, comment="Stack trace for errors")
    
    def __repr__(self):
        return f"<SystemEvent(type={self.event_type}, severity={self.severity})>"


class DataIntegrityCheck(BaseModel):
    """Data integrity verification records"""
    
    __tablename__ = "data_integrity_checks"
    
    table_name = Column(String(100), nullable=False, comment="Table being verified")
    record_id = Column(String(100), comment="Specific record ID (if applicable)")
    check_type = Column(String(50), nullable=False, comment="Type of integrity check")
    
    # Check Results
    passed = Column(Boolean, nullable=False, comment="Whether the check passed")
    expected_hash = Column(String(128), comment="Expected hash value")
    actual_hash = Column(String(128), comment="Actual calculated hash")
    
    # Check Details
    details = Column(JSONB, comment="Additional check details")
    performed_by = Column(Integer, ForeignKey("users.id"), comment="User who performed the check")
    
    # Relationships
    user = relationship("User", foreign_keys=[performed_by])
    
    def __repr__(self):
        return f"<DataIntegrityCheck(table={self.table_name}, passed={self.passed})>"


class ComplianceReport(BaseModel):
    """Compliance reporting and audit summary"""
    
    __tablename__ = "compliance_reports"
    
    report_type = Column(String(100), nullable=False, comment="Type of compliance report")
    report_period_start = Column(DateTime(timezone=True), nullable=False, comment="Report period start")
    report_period_end = Column(DateTime(timezone=True), nullable=False, comment="Report period end")
    
    # Report Content
    summary = Column(JSONB, nullable=False, comment="Report summary data")
    findings = Column(JSONB, comment="Compliance findings")
    recommendations = Column(JSONB, comment="Recommendations for improvement")
    
    # Report Status
    status = Column(String(50), default="draft", comment="Report status")
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="User who generated the report")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="User who approved the report")
    approved_at = Column(DateTime(timezone=True), comment="Report approval timestamp")
    
    # File Information
    file_path = Column(String(500), comment="Path to generated report file")
    file_hash = Column(String(128), comment="Report file hash for integrity")
    
    # Relationships
    generator = relationship("User", foreign_keys=[generated_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<ComplianceReport(type={self.report_type}, status={self.status})>"
