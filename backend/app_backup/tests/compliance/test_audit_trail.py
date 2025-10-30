# QMS Audit Trail Compliance Tests
# Test 21 CFR Part 11 audit trail requirements

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.audit import AuditLog, AuditAction
from app.models.user import User
from app.services.audit_service import AuditService


class TestAuditTrailCompliance:
    """Test audit trail for 21 CFR Part 11 compliance."""
    
    def test_audit_log_creation(self, db_session: Session, test_user: User):
        """Test that audit logs are created properly."""
        audit_service = AuditService()
        
        # Create an audit log entry
        audit_log = audit_service.log_action(
            user_id=test_user.id,
            username=test_user.username,
            action=AuditAction.CREATE,
            table_name="test_table",
            record_id="123",
            new_values={"field1": "value1", "field2": "value2"},
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            module="EDMS",
            reason="Test audit entry"
        )
        
        assert audit_log is not None
        assert audit_log.user_id == test_user.id
        assert audit_log.username == test_user.username
        assert audit_log.action == AuditAction.CREATE
        assert audit_log.table_name == "test_table"
        assert audit_log.record_id == "123"
        assert audit_log.new_values == {"field1": "value1", "field2": "value2"}
        assert audit_log.ip_address == "192.168.1.100"
        assert audit_log.module == "EDMS"
        assert audit_log.data_hash is not None
    
    def test_audit_log_immutability(self, db_session: Session):
        """Test that audit logs cannot be modified."""
        # Create audit log
        audit_log = AuditLog(
            user_id=1,
            username="testuser",
            action=AuditAction.CREATE,
            table_name="test",
            record_id="1",
            new_values={"test": "value"}
        )
        
        db_session.add(audit_log)
        db_session.commit()
        original_timestamp = audit_log.timestamp
        
        # Try to modify timestamp (should be prevented by database constraints)
        audit_log.timestamp = datetime.utcnow() + timedelta(hours=1)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_audit_trail_integrity(self, test_user: User):
        """Test audit trail data integrity verification."""
        audit_service = AuditService()
        
        # Create audit entry
        audit_log = audit_service.log_action(
            user_id=test_user.id,
            username=test_user.username,
            action=AuditAction.UPDATE,
            table_name="documents",
            record_id="DOC-001",
            old_values={"status": "draft"},
            new_values={"status": "approved"}
        )
        
        # Verify integrity
        assert audit_log.verify_integrity() is True
        
        # Test integrity verification method
        integrity_check = audit_service.verify_audit_integrity(audit_log.id)
        assert integrity_check["total_records"] == 1
        assert integrity_check["verified_records"] == 1
        assert integrity_check["integrity_percentage"] == 100.0
    
    def test_audit_trail_search(self, test_user: User):
        """Test audit trail search and filtering."""
        audit_service = AuditService()
        
        # Create multiple audit entries
        actions = [
            (AuditAction.CREATE, "documents", "DOC-001"),
            (AuditAction.UPDATE, "documents", "DOC-001"),
            (AuditAction.READ, "documents", "DOC-001"),
            (AuditAction.DELETE, "users", "USER-001")
        ]
        
        for action, table, record_id in actions:
            audit_service.log_action(
                user_id=test_user.id,
                username=test_user.username,
                action=action,
                table_name=table,
                record_id=record_id,
                module="EDMS"
            )
        
        # Test filtering by table
        doc_logs = audit_service.get_audit_trail(table_name="documents")
        assert len(doc_logs) == 3
        
        # Test filtering by user
        user_logs = audit_service.get_audit_trail(user_id=test_user.id)
        assert len(user_logs) == 4
        
        # Test filtering by action
        create_logs = audit_service.get_audit_trail(action=AuditAction.CREATE)
        assert len(create_logs) == 1
    
    def test_compliance_report_generation(self, test_user: User):
        """Test compliance report generation."""
        audit_service = AuditService()
        
        # Create audit data
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        audit_service.log_action(
            user_id=test_user.id,
            username=test_user.username,
            action=AuditAction.CREATE,
            table_name="documents",
            record_id="DOC-001",
            module="EDMS"
        )
        
        # Generate compliance report
        report = audit_service.generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            module="EDMS"
        )
        
        assert "report_period" in report
        assert "summary" in report
        assert "action_breakdown" in report
        assert "integrity_check" in report
        assert "compliance_status" in report
        
        assert report["compliance_status"] == "COMPLIANT"
        assert report["summary"]["total_activities"] >= 1


class TestDataIntegrity:
    """Test data integrity compliance features."""
    
    def test_hash_calculation(self):
        """Test data hash calculation for integrity."""
        from app.core.security import SecurityUtils
        
        test_data = "test data for hashing"
        hash1 = SecurityUtils.calculate_hash(test_data)
        hash2 = SecurityUtils.calculate_hash(test_data)
        
        # Same data should produce same hash
        assert hash1 == hash2
        
        # Different data should produce different hash
        different_data = "different test data"
        hash3 = SecurityUtils.calculate_hash(different_data)
        assert hash1 != hash3
    
    def test_audit_log_hash_verification(self, test_user: User):
        """Test audit log hash verification."""
        audit_service = AuditService()
        
        audit_log = audit_service.log_action(
            user_id=test_user.id,
            username=test_user.username,
            action=AuditAction.CREATE,
            table_name="test_table",
            record_id="123"
        )
        
        # Hash should be automatically calculated
        assert audit_log.data_hash is not None
        assert len(audit_log.data_hash) == 64  # SHA-256 hex length
        
        # Verification should pass
        assert audit_log.verify_integrity() is True


class TestAlcoaPrinciples:
    """Test ALCOA principles implementation."""
    
    def test_attributable(self, test_user: User):
        """Test that all actions are attributable to users."""
        audit_service = AuditService()
        
        audit_log = audit_service.log_action(
            user_id=test_user.id,
            username=test_user.username,
            action=AuditAction.CREATE,
            table_name="documents",
            record_id="DOC-001"
        )
        
        # Every action must be linked to a user
        assert audit_log.user_id is not None
        assert audit_log.username is not None
        assert audit_log.user_id == test_user.id
        assert audit_log.username == test_user.username
    
    def test_legible(self, test_user: User):
        """Test that audit data is legible and readable."""
        audit_service = AuditService()
        
        audit_log = audit_service.log_action(
            user_id=test_user.id,
            username=test_user.username,
            action=AuditAction.UPDATE,
            table_name="documents",
            record_id="DOC-001",
            old_values={"title": "Old Title"},
            new_values={"title": "New Title"}
        )
        
        # Data should be in readable format
        assert isinstance(audit_log.old_values, dict)
        assert isinstance(audit_log.new_values, dict)
        assert audit_log.old_values["title"] == "Old Title"
        assert audit_log.new_values["title"] == "New Title"
    
    def test_contemporaneous(self, test_user: User):
        """Test that audit records are created contemporaneously."""
        audit_service = AuditService()
        
        before_time = datetime.utcnow()
        
        audit_log = audit_service.log_action(
            user_id=test_user.id,
            username=test_user.username,
            action=AuditAction.CREATE,
            table_name="documents",
            record_id="DOC-001"
        )
        
        after_time = datetime.utcnow()
        
        # Audit log timestamp should be very close to action time
        assert before_time <= audit_log.timestamp <= after_time
        
        # Should be within reasonable time window (< 1 second)
        time_diff = (audit_log.timestamp - before_time).total_seconds()
        assert time_diff < 1.0
    
    def test_original(self, test_user: User):
        """Test that original data is preserved."""
        audit_service = AuditService()
        
        original_data = {
            "title": "Original Document Title",
            "content": "Original content",
            "version": "1.0"
        }
        
        audit_log = audit_service.log_action(
            user_id=test_user.id,
            username=test_user.username,
            action=AuditAction.CREATE,
            table_name="documents",
            record_id="DOC-001",
            new_values=original_data
        )
        
        # Original data should be preserved exactly
        assert audit_log.new_values == original_data
        
        # Data should not be modified in storage
        stored_data = audit_log.new_values
        assert stored_data["title"] == "Original Document Title"
        assert stored_data["content"] == "Original content"
        assert stored_data["version"] == "1.0"
    
    def test_accurate(self, test_user: User):
        """Test that audit data is accurate."""
        audit_service = AuditService()
        
        # Test data accuracy by verifying hash integrity
        test_values = {"field1": "value1", "field2": 42, "field3": True}
        
        audit_log = audit_service.log_action(
            user_id=test_user.id,
            username=test_user.username,
            action=AuditAction.CREATE,
            table_name="documents",
            record_id="DOC-001",
            new_values=test_values
        )
        
        # Data should be stored accurately
        assert audit_log.new_values == test_values
        
        # Hash should verify data accuracy
        assert audit_log.verify_integrity() is True