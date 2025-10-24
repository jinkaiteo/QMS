# QMS Audit Service
# Phase 1: Audit trail service for 21 CFR Part 11 compliance

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db_context
from app.models.audit import AuditLog, AuditAction
from app.core.security import SecurityUtils


class AuditService:
    """Service for managing audit trail and compliance logging"""
    
    def __init__(self):
        self.security_utils = SecurityUtils()
    
    def log_action(
        self,
        user_id: int,
        username: str,
        action: AuditAction,
        table_name: str,
        record_id: str = None,
        old_values: Dict[str, Any] = None,
        new_values: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None,
        module: str = None,
        reason: str = None,
        is_system_action: bool = False
    ) -> AuditLog:
        """
        Log an action to the audit trail
        
        Args:
            user_id: ID of the user performing the action
            username: Username of the user
            action: Type of action (CREATE, UPDATE, DELETE, etc.)
            table_name: Name of the affected database table
            record_id: ID of the affected record
            old_values: Previous values (for UPDATE operations)
            new_values: New values (for CREATE/UPDATE operations)
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session identifier
            module: QMS module (EDMS, QRM, TRM, LIMS, SYSTEM)
            reason: Reason for the action
            is_system_action: Whether this is a system-initiated action
        
        Returns:
            AuditLog: The created audit log entry
        """
        
        # Calculate data hash for integrity
        data_for_hash = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action.value if isinstance(action, AuditAction) else action,
            "table_name": table_name,
            "record_id": record_id,
            "old_values": old_values,
            "new_values": new_values
        }
        
        data_hash = self.security_utils.calculate_hash(str(data_for_hash))
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            module=module,
            reason=reason,
            data_hash=data_hash,
            is_system_action=is_system_action
        )
        
        # Save to database
        with get_db_context(user_id=user_id, ip_address=ip_address) as db:
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
        
        return audit_log
    
    def get_audit_trail(
        self,
        table_name: str = None,
        record_id: str = None,
        user_id: int = None,
        action: AuditAction = None,
        module: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Retrieve audit trail entries with filtering
        
        Args:
            table_name: Filter by table name
            record_id: Filter by record ID
            user_id: Filter by user ID
            action: Filter by action type
            module: Filter by module
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of records to return
            offset: Number of records to skip
        
        Returns:
            List[AuditLog]: List of audit log entries
        """
        
        db = SessionLocal()
        try:
            query = db.query(AuditLog)
            
            # Apply filters
            if table_name:
                query = query.filter(AuditLog.table_name == table_name)
            
            if record_id:
                query = query.filter(AuditLog.record_id == record_id)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if action:
                query = query.filter(AuditLog.action == action)
            
            if module:
                query = query.filter(AuditLog.module == module)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            # Order by timestamp (newest first) and apply pagination
            query = query.order_by(AuditLog.timestamp.desc())
            query = query.offset(offset).limit(limit)
            
            return query.all()
            
        finally:
            db.close()
    
    def verify_audit_integrity(
        self,
        audit_log_id: int = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Verify the integrity of audit log entries
        
        Args:
            audit_log_id: Specific audit log to verify (optional)
            start_date: Start date for range verification
            end_date: End date for range verification
        
        Returns:
            Dict containing verification results
        """
        
        db = SessionLocal()
        try:
            query = db.query(AuditLog)
            
            if audit_log_id:
                query = query.filter(AuditLog.id == audit_log_id)
            else:
                if start_date:
                    query = query.filter(AuditLog.timestamp >= start_date)
                if end_date:
                    query = query.filter(AuditLog.timestamp <= end_date)
            
            audit_logs = query.all()
            
            total_records = len(audit_logs)
            verified_records = 0
            failed_records = []
            
            for audit_log in audit_logs:
                if audit_log.verify_integrity():
                    verified_records += 1
                else:
                    failed_records.append({
                        "id": audit_log.id,
                        "timestamp": audit_log.timestamp,
                        "user_id": audit_log.user_id,
                        "action": audit_log.action
                    })
            
            return {
                "total_records": total_records,
                "verified_records": verified_records,
                "failed_records": len(failed_records),
                "integrity_percentage": (verified_records / total_records * 100) if total_records > 0 else 0,
                "failed_details": failed_records
            }
            
        finally:
            db.close()
    
    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        module: str = None
    ) -> Dict[str, Any]:
        """
        Generate a compliance report for audit activities
        
        Args:
            start_date: Report period start date
            end_date: Report period end date
            module: Specific module to report on (optional)
        
        Returns:
            Dict containing compliance report data
        """
        
        audit_logs = self.get_audit_trail(
            module=module,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # High limit for reporting
        )
        
        # Analyze audit data
        action_counts = {}
        user_activity = {}
        daily_activity = {}
        
        for log in audit_logs:
            # Count actions
            action_key = log.action.value if hasattr(log.action, 'value') else str(log.action)
            action_counts[action_key] = action_counts.get(action_key, 0) + 1
            
            # Count user activity
            user_key = f"{log.username} ({log.user_id})"
            user_activity[user_key] = user_activity.get(user_key, 0) + 1
            
            # Count daily activity
            day_key = log.timestamp.date().isoformat()
            daily_activity[day_key] = daily_activity.get(day_key, 0) + 1
        
        # Verify integrity
        integrity_check = self.verify_audit_integrity(start_date=start_date, end_date=end_date)
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "module": module
            },
            "summary": {
                "total_activities": len(audit_logs),
                "unique_users": len(user_activity),
                "unique_days": len(daily_activity)
            },
            "action_breakdown": action_counts,
            "user_activity": user_activity,
            "daily_activity": daily_activity,
            "integrity_check": integrity_check,
            "compliance_status": "COMPLIANT" if integrity_check["integrity_percentage"] == 100 else "NON_COMPLIANT"
        }
