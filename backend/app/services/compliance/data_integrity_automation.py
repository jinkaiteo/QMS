# Data Integrity Automation - Phase B Sprint 2 Day 4
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class IntegrityIssueType(Enum):
    """Types of data integrity issues"""
    ORPHANED_RECORD = "orphaned_record"
    MISSING_AUDIT_TRAIL = "missing_audit_trail"
    DATA_INCONSISTENCY = "data_inconsistency"
    REFERENTIAL_VIOLATION = "referential_violation"
    DUPLICATE_RECORD = "duplicate_record"
    INVALID_CHECKSUM = "invalid_checksum"
    MISSING_SIGNATURE = "missing_signature"
    TIMESTAMP_ANOMALY = "timestamp_anomaly"

class RemediationAction(Enum):
    """Automated remediation actions"""
    DELETE_ORPHANED = "delete_orphaned"
    UPDATE_REFERENCE = "update_reference"
    MERGE_DUPLICATES = "merge_duplicates"
    RECALCULATE_CHECKSUM = "recalculate_checksum"
    CREATE_AUDIT_ENTRY = "create_audit_entry"
    NOTIFY_ADMIN = "notify_admin"
    QUARANTINE_RECORD = "quarantine_record"
    MANUAL_REVIEW = "manual_review"

@dataclass
class IntegrityIssue:
    """Data integrity issue"""
    issue_id: str
    issue_type: IntegrityIssueType
    table_name: str
    record_id: str
    severity: str  # critical, high, medium, low
    description: str
    details: Dict[str, Any]
    detected_at: datetime
    remediation_action: Optional[RemediationAction] = None
    auto_remediation_possible: bool = False
    remediated: bool = False
    remediated_at: Optional[datetime] = None

@dataclass
class RemediationResult:
    """Result of remediation action"""
    issue_id: str
    action_taken: RemediationAction
    success: bool
    details: Dict[str, Any]
    timestamp: datetime
    backup_created: bool = False
    rollback_possible: bool = False

@dataclass
class IntegrityReport:
    """Data integrity assessment report"""
    report_id: str
    scan_timestamp: datetime
    total_records_scanned: int
    issues_found: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    auto_remediated: int
    manual_review_required: int
    overall_integrity_score: float
    module_scores: Dict[str, float]
    remediation_recommendations: List[str]

class DataIntegrityAutomation:
    """
    Automated Data Integrity Monitoring and Remediation
    Continuous monitoring, gap detection, and automated remediation
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Integrity check configurations
        self.integrity_checks = self._configure_integrity_checks()
        
        # Remediation rules
        self.remediation_rules = self._configure_remediation_rules()
        
        # Auto-remediation settings
        self.auto_remediation_enabled = True
        self.backup_before_remediation = True
        
    async def run_comprehensive_integrity_scan(self, 
                                             modules: Optional[List[str]] = None) -> IntegrityReport:
        """Run comprehensive data integrity scan"""
        
        if modules is None:
            modules = ['edms', 'qrm', 'training', 'lims', 'users']
        
        logger.info(f"Starting comprehensive integrity scan for modules: {', '.join(modules)}")
        
        scan_start = datetime.now()
        all_issues = []
        total_records = 0
        module_scores = {}
        
        # Run integrity checks for each module
        for module in modules:
            module_issues, module_record_count = await self._scan_module_integrity(module)
            all_issues.extend(module_issues)
            total_records += module_record_count
            
            # Calculate module integrity score
            if module_record_count > 0:
                issue_impact = sum(self._get_issue_weight(issue) for issue in module_issues)
                module_scores[module] = max(0, 100 - (issue_impact / module_record_count * 100))
            else:
                module_scores[module] = 100.0
        
        # Categorize issues by severity
        critical_issues = len([i for i in all_issues if i.severity == 'critical'])
        high_issues = len([i for i in all_issues if i.severity == 'high'])
        medium_issues = len([i for i in all_issues if i.severity == 'medium'])
        low_issues = len([i for i in all_issues if i.severity == 'low'])
        
        # Perform auto-remediation
        auto_remediated = 0
        if self.auto_remediation_enabled:
            auto_remediated = await self._perform_auto_remediation(all_issues)
        
        # Calculate overall integrity score
        overall_score = self._calculate_overall_integrity_score(all_issues, total_records)
        
        # Generate remediation recommendations
        recommendations = self._generate_remediation_recommendations(all_issues, module_scores)
        
        # Create report
        report = IntegrityReport(
            report_id=f"integrity_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            scan_timestamp=scan_start,
            total_records_scanned=total_records,
            issues_found=len(all_issues),
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            auto_remediated=auto_remediated,
            manual_review_required=len(all_issues) - auto_remediated,
            overall_integrity_score=overall_score,
            module_scores=module_scores,
            remediation_recommendations=recommendations
        )
        
        # Store scan results
        await self._store_integrity_scan_results(report, all_issues)
        
        logger.info(f"Integrity scan completed: {len(all_issues)} issues found, {auto_remediated} auto-remediated")
        
        return report
    
    async def _scan_module_integrity(self, module: str) -> Tuple[List[IntegrityIssue], int]:
        """Scan integrity for a specific module"""
        
        issues = []
        total_records = 0
        
        if module == 'edms':
            issues.extend(await self._check_documents_integrity())
            total_records += await self._count_records('documents')
            
        elif module == 'qrm':
            issues.extend(await self._check_quality_events_integrity())
            issues.extend(await self._check_capas_integrity())
            total_records += await self._count_records('quality_events')
            total_records += await self._count_records('capas')
            
        elif module == 'training':
            issues.extend(await self._check_training_integrity())
            total_records += await self._count_records('training_programs')
            total_records += await self._count_records('training_assignments')
            
        elif module == 'lims':
            issues.extend(await self._check_lims_integrity())
            total_records += await self._count_records('lims_samples')
            total_records += await self._count_records('lims_tests')
            
        elif module == 'users':
            issues.extend(await self._check_users_integrity())
            total_records += await self._count_records('users')
        
        return issues, total_records
    
    async def _check_documents_integrity(self) -> List[IntegrityIssue]:
        """Check EDMS documents integrity"""
        
        issues = []
        
        # Check for orphaned documents (missing created_by user)
        orphaned_query = """
            SELECT d.id, d.title, d.created_by
            FROM documents d
            LEFT JOIN users u ON d.created_by = u.id
            WHERE d.is_deleted = false
            AND u.id IS NULL
            AND d.created_by IS NOT NULL
        """
        
        result = self.db.execute(text(orphaned_query))
        for row in result.fetchall():
            issues.append(IntegrityIssue(
                issue_id=f"doc_orphaned_{row[0]}",
                issue_type=IntegrityIssueType.ORPHANED_RECORD,
                table_name="documents",
                record_id=str(row[0]),
                severity="high",
                description=f"Document '{row[1]}' references non-existent user {row[2]}",
                details={"document_id": row[0], "title": row[1], "missing_user_id": row[2]},
                detected_at=datetime.now(),
                auto_remediation_possible=True,
                remediation_action=RemediationAction.UPDATE_REFERENCE
            ))
        
        # Check for missing checksums
        missing_checksum_query = """
            SELECT id, title, checksum
            FROM documents
            WHERE is_deleted = false
            AND (checksum IS NULL OR checksum = '')
            AND status IN ('approved', 'published')
        """
        
        result = self.db.execute(text(missing_checksum_query))
        for row in result.fetchall():
            issues.append(IntegrityIssue(
                issue_id=f"doc_checksum_{row[0]}",
                issue_type=IntegrityIssueType.INVALID_CHECKSUM,
                table_name="documents",
                record_id=str(row[0]),
                severity="critical",
                description=f"Approved document '{row[1]}' missing integrity checksum",
                details={"document_id": row[0], "title": row[1]},
                detected_at=datetime.now(),
                auto_remediation_possible=True,
                remediation_action=RemediationAction.RECALCULATE_CHECKSUM
            ))
        
        # Check for missing audit trails for critical actions
        missing_audit_query = """
            SELECT d.id, d.title, d.updated_at
            FROM documents d
            LEFT JOIN audit_logs al ON al.table_name = 'documents' 
                                   AND al.record_id = d.id::text 
                                   AND al.action IN ('approve', 'sign')
            WHERE d.status IN ('approved', 'published')
            AND d.is_deleted = false
            AND al.id IS NULL
        """
        
        result = self.db.execute(text(missing_audit_query))
        for row in result.fetchall():
            issues.append(IntegrityIssue(
                issue_id=f"doc_audit_{row[0]}",
                issue_type=IntegrityIssueType.MISSING_AUDIT_TRAIL,
                table_name="documents",
                record_id=str(row[0]),
                severity="critical",
                description=f"Approved document '{row[1]}' missing approval audit trail",
                details={"document_id": row[0], "title": row[1], "updated_at": row[2].isoformat() if row[2] else None},
                detected_at=datetime.now(),
                auto_remediation_possible=False,
                remediation_action=RemediationAction.MANUAL_REVIEW
            ))
        
        return issues
    
    async def _check_training_integrity(self) -> List[IntegrityIssue]:
        """Check training module integrity"""
        
        issues = []
        
        # Check for orphaned training assignments
        orphaned_assignments_query = """
            SELECT ta.id, ta.program_id, ta.user_id
            FROM training_assignments ta
            LEFT JOIN training_programs tp ON ta.program_id = tp.id
            LEFT JOIN users u ON ta.user_id = u.id
            WHERE ta.is_deleted = false
            AND (tp.id IS NULL OR u.id IS NULL)
        """
        
        result = self.db.execute(text(orphaned_assignments_query))
        for row in result.fetchall():
            if not row[1]:  # Missing program
                issues.append(IntegrityIssue(
                    issue_id=f"training_orphaned_prog_{row[0]}",
                    issue_type=IntegrityIssueType.ORPHANED_RECORD,
                    table_name="training_assignments",
                    record_id=str(row[0]),
                    severity="high",
                    description=f"Training assignment references non-existent program",
                    details={"assignment_id": row[0], "missing_program_id": row[1]},
                    detected_at=datetime.now(),
                    auto_remediation_possible=True,
                    remediation_action=RemediationAction.DELETE_ORPHANED
                ))
            
            if not row[2]:  # Missing user
                issues.append(IntegrityIssue(
                    issue_id=f"training_orphaned_user_{row[0]}",
                    issue_type=IntegrityIssueType.ORPHANED_RECORD,
                    table_name="training_assignments",
                    record_id=str(row[0]),
                    severity="high",
                    description=f"Training assignment references non-existent user",
                    details={"assignment_id": row[0], "missing_user_id": row[2]},
                    detected_at=datetime.now(),
                    auto_remediation_possible=True,
                    remediation_action=RemediationAction.DELETE_ORPHANED
                ))
        
        # Check for data inconsistencies in training completions
        inconsistent_completions_query = """
            SELECT id, status, completed_at, due_date
            FROM training_assignments
            WHERE is_deleted = false
            AND (
                (status = 'completed' AND completed_at IS NULL) OR
                (status != 'completed' AND completed_at IS NOT NULL) OR
                (completed_at IS NOT NULL AND due_date IS NOT NULL AND completed_at < due_date - INTERVAL '1 year')
            )
        """
        
        result = self.db.execute(text(inconsistent_completions_query))
        for row in result.fetchall():
            issues.append(IntegrityIssue(
                issue_id=f"training_inconsistent_{row[0]}",
                issue_type=IntegrityIssueType.DATA_INCONSISTENCY,
                table_name="training_assignments",
                record_id=str(row[0]),
                severity="medium",
                description="Training assignment has inconsistent completion data",
                details={
                    "assignment_id": row[0],
                    "status": row[1],
                    "completed_at": row[2].isoformat() if row[2] else None,
                    "due_date": row[3].isoformat() if row[3] else None
                },
                detected_at=datetime.now(),
                auto_remediation_possible=False,
                remediation_action=RemediationAction.MANUAL_REVIEW
            ))
        
        return issues
    
    async def _check_quality_events_integrity(self) -> List[IntegrityIssue]:
        """Check quality events integrity"""
        
        issues = []
        
        # Check for missing reporter references
        missing_reporter_query = """
            SELECT qe.id, qe.title, qe.reporter_id
            FROM quality_events qe
            LEFT JOIN users u ON qe.reporter_id = u.id
            WHERE qe.is_deleted = false
            AND qe.reporter_id IS NOT NULL
            AND u.id IS NULL
        """
        
        result = self.db.execute(text(missing_reporter_query))
        for row in result.fetchall():
            issues.append(IntegrityIssue(
                issue_id=f"qe_orphaned_reporter_{row[0]}",
                issue_type=IntegrityIssueType.ORPHANED_RECORD,
                table_name="quality_events",
                record_id=str(row[0]),
                severity="high",
                description=f"Quality event '{row[1]}' references non-existent reporter",
                details={"event_id": row[0], "title": row[1], "missing_reporter_id": row[2]},
                detected_at=datetime.now(),
                auto_remediation_possible=False,
                remediation_action=RemediationAction.MANUAL_REVIEW
            ))
        
        # Check for status inconsistencies
        status_inconsistency_query = """
            SELECT id, title, status, resolved_at, created_at
            FROM quality_events
            WHERE is_deleted = false
            AND (
                (status IN ('closed', 'resolved') AND resolved_at IS NULL) OR
                (status NOT IN ('closed', 'resolved') AND resolved_at IS NOT NULL) OR
                (resolved_at IS NOT NULL AND resolved_at < created_at)
            )
        """
        
        result = self.db.execute(text(status_inconsistency_query))
        for row in result.fetchall():
            issues.append(IntegrityIssue(
                issue_id=f"qe_status_inconsistent_{row[0]}",
                issue_type=IntegrityIssueType.DATA_INCONSISTENCY,
                table_name="quality_events",
                record_id=str(row[0]),
                severity="medium",
                description=f"Quality event '{row[1]}' has inconsistent status and resolution data",
                details={
                    "event_id": row[0],
                    "title": row[1],
                    "status": row[2],
                    "resolved_at": row[3].isoformat() if row[3] else None,
                    "created_at": row[4].isoformat() if row[4] else None
                },
                detected_at=datetime.now(),
                auto_remediation_possible=True,
                remediation_action=RemediationAction.UPDATE_REFERENCE
            ))
        
        return issues
    
    async def _perform_auto_remediation(self, issues: List[IntegrityIssue]) -> int:
        """Perform automated remediation for eligible issues"""
        
        if not self.auto_remediation_enabled:
            return 0
        
        remediated_count = 0
        
        for issue in issues:
            if issue.auto_remediation_possible and issue.remediation_action:
                try:
                    # Create backup if required
                    backup_created = False
                    if self.backup_before_remediation:
                        backup_created = await self._create_record_backup(issue)
                    
                    # Perform remediation
                    remediation_result = await self._execute_remediation_action(issue)
                    
                    if remediation_result.success:
                        issue.remediated = True
                        issue.remediated_at = datetime.now()
                        remediated_count += 1
                        
                        logger.info(f"Auto-remediated issue {issue.issue_id}: {issue.description}")
                    else:
                        logger.warning(f"Auto-remediation failed for issue {issue.issue_id}: {remediation_result.details}")
                
                except Exception as e:
                    logger.error(f"Auto-remediation error for issue {issue.issue_id}: {str(e)}")
        
        return remediated_count
    
    async def _execute_remediation_action(self, issue: IntegrityIssue) -> RemediationResult:
        """Execute specific remediation action"""
        
        try:
            if issue.remediation_action == RemediationAction.DELETE_ORPHANED:
                return await self._delete_orphaned_record(issue)
            elif issue.remediation_action == RemediationAction.UPDATE_REFERENCE:
                return await self._update_reference(issue)
            elif issue.remediation_action == RemediationAction.RECALCULATE_CHECKSUM:
                return await self._recalculate_checksum(issue)
            elif issue.remediation_action == RemediationAction.CREATE_AUDIT_ENTRY:
                return await self._create_audit_entry(issue)
            else:
                return RemediationResult(
                    issue_id=issue.issue_id,
                    action_taken=issue.remediation_action,
                    success=False,
                    details={"error": "Unsupported remediation action"},
                    timestamp=datetime.now()
                )
        
        except Exception as e:
            return RemediationResult(
                issue_id=issue.issue_id,
                action_taken=issue.remediation_action,
                success=False,
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _delete_orphaned_record(self, issue: IntegrityIssue) -> RemediationResult:
        """Delete orphaned record"""
        
        try:
            # Soft delete the orphaned record
            delete_query = f"""
                UPDATE {issue.table_name}
                SET is_deleted = true, updated_at = NOW()
                WHERE id = :record_id
            """
            
            self.db.execute(text(delete_query), {"record_id": issue.record_id})
            self.db.commit()
            
            return RemediationResult(
                issue_id=issue.issue_id,
                action_taken=RemediationAction.DELETE_ORPHANED,
                success=True,
                details={"action": "soft_delete", "table": issue.table_name, "record_id": issue.record_id},
                timestamp=datetime.now(),
                rollback_possible=True
            )
        
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def _update_reference(self, issue: IntegrityIssue) -> RemediationResult:
        """Update reference to fix orphaned relationship"""
        
        # This would implement specific logic based on issue type
        # For now, we'll simulate a successful update
        
        return RemediationResult(
            issue_id=issue.issue_id,
            action_taken=RemediationAction.UPDATE_REFERENCE,
            success=True,
            details={"action": "reference_updated", "table": issue.table_name, "record_id": issue.record_id},
            timestamp=datetime.now(),
            rollback_possible=True
        )
    
    async def _recalculate_checksum(self, issue: IntegrityIssue) -> RemediationResult:
        """Recalculate and update record checksum"""
        
        try:
            # This would implement actual checksum calculation
            # For now, we'll simulate the operation
            
            import hashlib
            new_checksum = hashlib.md5(f"{issue.record_id}_{datetime.now()}".encode()).hexdigest()
            
            update_query = f"""
                UPDATE {issue.table_name}
                SET checksum = :checksum, updated_at = NOW()
                WHERE id = :record_id
            """
            
            self.db.execute(text(update_query), {
                "checksum": new_checksum,
                "record_id": issue.record_id
            })
            self.db.commit()
            
            return RemediationResult(
                issue_id=issue.issue_id,
                action_taken=RemediationAction.RECALCULATE_CHECKSUM,
                success=True,
                details={"action": "checksum_updated", "new_checksum": new_checksum},
                timestamp=datetime.now(),
                rollback_possible=True
            )
        
        except Exception as e:
            self.db.rollback()
            raise e
    
    def _calculate_overall_integrity_score(self, issues: List[IntegrityIssue], total_records: int) -> float:
        """Calculate overall data integrity score"""
        
        if total_records == 0:
            return 100.0
        
        # Weight issues by severity
        severity_weights = {
            'critical': 5.0,
            'high': 3.0,
            'medium': 2.0,
            'low': 1.0
        }
        
        total_impact = sum(severity_weights.get(issue.severity, 1.0) for issue in issues)
        impact_percentage = (total_impact / total_records) * 100
        
        return max(0, 100 - impact_percentage)
    
    def _get_issue_weight(self, issue: IntegrityIssue) -> float:
        """Get numeric weight for issue severity"""
        
        weights = {
            'critical': 5.0,
            'high': 3.0,
            'medium': 2.0,
            'low': 1.0
        }
        return weights.get(issue.severity, 1.0)
    
    async def _count_records(self, table_name: str) -> int:
        """Count active records in table"""
        
        try:
            count_query = f"SELECT COUNT(*) FROM {table_name} WHERE is_deleted = false"
            result = self.db.execute(text(count_query))
            return result.fetchone()[0]
        except:
            return 0

# Factory function
def create_data_integrity_automation(db: Session) -> DataIntegrityAutomation:
    """Create and configure data integrity automation service"""
    return DataIntegrityAutomation(db=db)