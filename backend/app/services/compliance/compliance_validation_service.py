# Compliance Validation Service - Phase B Sprint 2 Day 3
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

@dataclass
class DataIntegrityCheck:
    """Data integrity validation result"""
    check_name: str
    table_name: str
    status: str  # 'passed', 'failed', 'warning'
    details: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)

@dataclass
class ComplianceValidationResult:
    """Comprehensive compliance validation result"""
    validation_id: str
    validation_timestamp: datetime
    overall_compliance_score: float
    cfr_part11_compliance: Dict[str, Any]
    iso13485_compliance: Dict[str, Any]
    data_integrity_checks: List[DataIntegrityCheck]
    audit_trail_validation: Dict[str, Any]
    security_compliance: Dict[str, Any]
    recommendations: List[str]
    critical_issues: List[str]
    next_validation_due: datetime

class ComplianceValidationService:
    """
    Comprehensive Compliance Validation Service
    Validates data integrity, audit trails, and regulatory compliance
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def perform_comprehensive_validation(self, 
                                             validation_scope: List[str] = None,
                                             include_data_integrity: bool = True,
                                             include_audit_validation: bool = True) -> ComplianceValidationResult:
        """
        Perform comprehensive compliance validation
        
        Args:
            validation_scope: Modules to validate (edms, qrm, training, lims)
            include_data_integrity: Whether to run data integrity checks
            include_audit_validation: Whether to validate audit trails
            
        Returns:
            Complete validation result with scores and recommendations
        """
        validation_id = f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if validation_scope is None:
            validation_scope = ['edms', 'qrm', 'training', 'lims']
        
        logger.info(f"Starting comprehensive compliance validation {validation_id}")
        
        # CFR Part 11 Compliance Validation
        cfr_compliance = await self._validate_cfr_part11_compliance(validation_scope)
        
        # ISO 13485 Compliance Validation
        iso_compliance = await self._validate_iso13485_compliance(validation_scope)
        
        # Data Integrity Checks
        data_integrity_checks = []
        if include_data_integrity:
            data_integrity_checks = await self._perform_data_integrity_checks(validation_scope)
        
        # Audit Trail Validation
        audit_validation = {}
        if include_audit_validation:
            audit_validation = await self._validate_audit_trails(validation_scope)
        
        # Security Compliance Check
        security_compliance = await self._validate_security_compliance()
        
        # Calculate overall compliance score
        overall_score = self._calculate_overall_compliance_score(
            cfr_compliance, iso_compliance, data_integrity_checks, 
            audit_validation, security_compliance
        )
        
        # Generate recommendations
        recommendations = self._generate_compliance_recommendations(
            cfr_compliance, iso_compliance, data_integrity_checks, 
            audit_validation, security_compliance
        )
        
        # Identify critical issues
        critical_issues = self._identify_critical_issues(
            cfr_compliance, iso_compliance, data_integrity_checks, 
            audit_validation, security_compliance
        )
        
        # Calculate next validation due date
        next_due = self._calculate_next_validation_date(overall_score, critical_issues)
        
        return ComplianceValidationResult(
            validation_id=validation_id,
            validation_timestamp=datetime.now(),
            overall_compliance_score=overall_score,
            cfr_part11_compliance=cfr_compliance,
            iso13485_compliance=iso_compliance,
            data_integrity_checks=data_integrity_checks,
            audit_trail_validation=audit_validation,
            security_compliance=security_compliance,
            recommendations=recommendations,
            critical_issues=critical_issues,
            next_validation_due=next_due
        )
    
    async def _validate_cfr_part11_compliance(self, validation_scope: List[str]) -> Dict[str, Any]:
        """Validate 21 CFR Part 11 compliance across modules"""
        
        cfr_compliance = {
            'overall_status': 'compliant',
            'compliance_percentage': 0.0,
            'electronic_records': {},
            'electronic_signatures': {},
            'system_controls': {},
            'audit_trails': {},
            'issues': []
        }
        
        # Electronic Records Validation
        electronic_records = await self._validate_electronic_records(validation_scope)
        cfr_compliance['electronic_records'] = electronic_records
        
        # Electronic Signatures Validation
        electronic_signatures = await self._validate_electronic_signatures(validation_scope)
        cfr_compliance['electronic_signatures'] = electronic_signatures
        
        # System Controls Validation
        system_controls = await self._validate_system_controls(validation_scope)
        cfr_compliance['system_controls'] = system_controls
        
        # Audit Trail Validation for CFR compliance
        audit_trails = await self._validate_cfr_audit_trails(validation_scope)
        cfr_compliance['audit_trails'] = audit_trails
        
        # Calculate CFR compliance percentage
        compliance_scores = [
            electronic_records.get('compliance_score', 0),
            electronic_signatures.get('compliance_score', 0),
            system_controls.get('compliance_score', 0),
            audit_trails.get('compliance_score', 0)
        ]
        
        cfr_compliance['compliance_percentage'] = sum(compliance_scores) / len(compliance_scores)
        cfr_compliance['overall_status'] = 'compliant' if cfr_compliance['compliance_percentage'] >= 95 else 'non_compliant'
        
        return cfr_compliance
    
    async def _validate_electronic_records(self, validation_scope: List[str]) -> Dict[str, Any]:
        """Validate electronic records compliance"""
        
        validation_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN checksum IS NOT NULL THEN 1 END) as checksummed_records,
                COUNT(CASE WHEN created_by IS NOT NULL THEN 1 END) as attributed_records,
                COUNT(CASE WHEN created_at IS NOT NULL THEN 1 END) as timestamped_records,
                COUNT(CASE WHEN is_deleted = false THEN 1 END) as active_records
            FROM (
                SELECT id, checksum, created_by, created_at, is_deleted FROM documents
                UNION ALL
                SELECT id, checksum, created_by, created_at, is_deleted FROM quality_events
                UNION ALL
                SELECT id, checksum, created_by, created_at, is_deleted FROM training_programs
                UNION ALL
                SELECT id, checksum, created_by, created_at, is_deleted FROM lims_samples
            ) combined_records
        """
        
        result = self.db.execute(text(validation_query))
        record_data = dict(zip(result.keys(), result.fetchone() or [0]*5))
        
        total_records = record_data.get('total_records', 0)
        
        if total_records == 0:
            return {
                'compliance_score': 0,
                'status': 'no_data',
                'details': 'No electronic records found for validation'
            }
        
        # Calculate compliance percentages
        checksum_percentage = (record_data.get('checksummed_records', 0) / total_records) * 100
        attribution_percentage = (record_data.get('attributed_records', 0) / total_records) * 100
        timestamp_percentage = (record_data.get('timestamped_records', 0) / total_records) * 100
        
        # Overall compliance score for electronic records
        compliance_score = (checksum_percentage + attribution_percentage + timestamp_percentage) / 3
        
        return {
            'compliance_score': round(compliance_score, 2),
            'status': 'compliant' if compliance_score >= 95 else 'non_compliant',
            'total_records': total_records,
            'checksum_coverage': round(checksum_percentage, 2),
            'attribution_coverage': round(attribution_percentage, 2),
            'timestamp_coverage': round(timestamp_percentage, 2),
            'details': {
                'checksummed_records': record_data.get('checksummed_records', 0),
                'attributed_records': record_data.get('attributed_records', 0),
                'timestamped_records': record_data.get('timestamped_records', 0),
                'active_records': record_data.get('active_records', 0)
            }
        }
    
    async def _validate_electronic_signatures(self, validation_scope: List[str]) -> Dict[str, Any]:
        """Validate electronic signatures compliance"""
        
        signature_query = """
            SELECT 
                COUNT(*) as total_signature_events,
                COUNT(CASE WHEN signature_data IS NOT NULL THEN 1 END) as signed_events,
                COUNT(CASE WHEN signature_valid = true THEN 1 END) as valid_signatures,
                COUNT(CASE WHEN signature_algorithm IS NOT NULL THEN 1 END) as algorithmic_signatures,
                COUNT(CASE WHEN signer_certificate IS NOT NULL THEN 1 END) as certified_signatures
            FROM audit_logs
            WHERE action IN ('approve', 'sign', 'authorize', 'verify')
            AND created_at >= NOW() - INTERVAL '90 days'
        """
        
        result = self.db.execute(text(signature_query))
        signature_data = dict(zip(result.keys(), result.fetchone() or [0]*5))
        
        total_signature_events = signature_data.get('total_signature_events', 0)
        
        if total_signature_events == 0:
            return {
                'compliance_score': 100,  # No signature events means compliant by default
                'status': 'no_signatures',
                'details': 'No electronic signature events found in the validation period'
            }
        
        # Calculate signature compliance percentages
        signature_coverage = (signature_data.get('signed_events', 0) / total_signature_events) * 100
        validity_percentage = (signature_data.get('valid_signatures', 0) / max(signature_data.get('signed_events', 1), 1)) * 100
        algorithm_coverage = (signature_data.get('algorithmic_signatures', 0) / max(signature_data.get('signed_events', 1), 1)) * 100
        certificate_coverage = (signature_data.get('certified_signatures', 0) / max(signature_data.get('signed_events', 1), 1)) * 100
        
        # Overall signature compliance score
        compliance_score = (signature_coverage + validity_percentage + algorithm_coverage + certificate_coverage) / 4
        
        return {
            'compliance_score': round(compliance_score, 2),
            'status': 'compliant' if compliance_score >= 90 else 'non_compliant',
            'total_signature_events': total_signature_events,
            'signature_coverage': round(signature_coverage, 2),
            'validity_percentage': round(validity_percentage, 2),
            'algorithm_coverage': round(algorithm_coverage, 2),
            'certificate_coverage': round(certificate_coverage, 2),
            'details': signature_data
        }
    
    async def _perform_data_integrity_checks(self, validation_scope: List[str]) -> List[DataIntegrityCheck]:
        """Perform comprehensive data integrity checks"""
        
        integrity_checks = []
        
        # Check 1: Orphaned Records
        orphaned_check = await self._check_orphaned_records(validation_scope)
        integrity_checks.append(orphaned_check)
        
        # Check 2: Data Consistency
        consistency_check = await self._check_data_consistency(validation_scope)
        integrity_checks.append(consistency_check)
        
        # Check 3: Referential Integrity
        referential_check = await self._check_referential_integrity(validation_scope)
        integrity_checks.append(referential_check)
        
        # Check 4: Duplicate Detection
        duplicate_check = await self._check_duplicate_records(validation_scope)
        integrity_checks.append(duplicate_check)
        
        # Check 5: Data Completeness
        completeness_check = await self._check_data_completeness(validation_scope)
        integrity_checks.append(completeness_check)
        
        # Check 6: Audit Trail Completeness
        audit_completeness_check = await self._check_audit_trail_completeness(validation_scope)
        integrity_checks.append(audit_completeness_check)
        
        return integrity_checks
    
    async def _check_orphaned_records(self, validation_scope: List[str]) -> DataIntegrityCheck:
        """Check for orphaned records across the system"""
        
        orphaned_query = """
            SELECT 
                'training_assignments' as table_name,
                COUNT(*) as orphaned_count
            FROM training_assignments ta
            LEFT JOIN training_programs tp ON ta.program_id = tp.id
            LEFT JOIN users u ON ta.user_id = u.id
            WHERE tp.id IS NULL OR u.id IS NULL
            
            UNION ALL
            
            SELECT 
                'quality_events' as table_name,
                COUNT(*) as orphaned_count
            FROM quality_events qe
            LEFT JOIN users u ON qe.reporter_id = u.id
            WHERE u.id IS NULL
            
            UNION ALL
            
            SELECT 
                'capas' as table_name,
                COUNT(*) as orphaned_count
            FROM capas c
            LEFT JOIN quality_events qe ON c.quality_event_id = qe.id
            WHERE qe.id IS NULL
            
            UNION ALL
            
            SELECT 
                'documents' as table_name,
                COUNT(*) as orphaned_count
            FROM documents d
            LEFT JOIN users u ON d.created_by = u.id
            WHERE u.id IS NULL
        """
        
        result = self.db.execute(text(orphaned_query))
        orphaned_data = result.fetchall()
        
        total_orphaned = sum(row[1] for row in orphaned_data)
        orphaned_details = {row[0]: row[1] for row in orphaned_data}
        
        status = 'passed' if total_orphaned == 0 else 'failed'
        recommendations = []
        
        if total_orphaned > 0:
            recommendations = [
                'Review and clean up orphaned records',
                'Implement foreign key constraints to prevent orphaned records',
                'Add data validation checks in application logic'
            ]
        
        return DataIntegrityCheck(
            check_name='Orphaned Records Check',
            table_name='multiple',
            status=status,
            details={
                'total_orphaned_records': total_orphaned,
                'orphaned_by_table': orphaned_details,
                'severity': 'high' if total_orphaned > 10 else 'medium' if total_orphaned > 0 else 'low'
            },
            recommendations=recommendations
        )
    
    async def _check_data_consistency(self, validation_scope: List[str]) -> DataIntegrityCheck:
        """Check data consistency across related tables"""
        
        consistency_issues = []
        
        # Check training assignment status consistency
        training_consistency = """
            SELECT COUNT(*) as inconsistent_assignments
            FROM training_assignments ta
            JOIN training_programs tp ON ta.program_id = tp.id
            WHERE ta.status = 'completed' 
            AND ta.completed_at IS NULL
        """
        
        result = self.db.execute(text(training_consistency))
        training_issues = result.fetchone()[0]
        
        if training_issues > 0:
            consistency_issues.append({
                'issue': 'Training assignments marked complete without completion date',
                'count': training_issues,
                'table': 'training_assignments'
            })
        
        # Check quality event status consistency
        quality_consistency = """
            SELECT COUNT(*) as inconsistent_events
            FROM quality_events qe
            WHERE qe.status = 'closed'
            AND qe.resolved_at IS NULL
        """
        
        result = self.db.execute(text(quality_consistency))
        quality_issues = result.fetchone()[0]
        
        if quality_issues > 0:
            consistency_issues.append({
                'issue': 'Quality events marked closed without resolution date',
                'count': quality_issues,
                'table': 'quality_events'
            })
        
        total_issues = len(consistency_issues)
        status = 'passed' if total_issues == 0 else 'warning' if total_issues < 5 else 'failed'
        
        recommendations = []
        if consistency_issues:
            recommendations = [
                'Implement data validation rules for status changes',
                'Add database constraints for date consistency',
                'Review business logic for status updates'
            ]
        
        return DataIntegrityCheck(
            check_name='Data Consistency Check',
            table_name='multiple',
            status=status,
            details={
                'total_consistency_issues': total_issues,
                'issues_by_category': consistency_issues,
                'severity': 'high' if total_issues > 10 else 'medium' if total_issues > 0 else 'low'
            },
            recommendations=recommendations
        )
    
    def _calculate_overall_compliance_score(self, 
                                          cfr_compliance: Dict[str, Any],
                                          iso_compliance: Dict[str, Any],
                                          data_integrity_checks: List[DataIntegrityCheck],
                                          audit_validation: Dict[str, Any],
                                          security_compliance: Dict[str, Any]) -> float:
        """Calculate overall compliance score"""
        
        # Weight different compliance areas
        weights = {
            'cfr_part11': 0.3,
            'iso13485': 0.25,
            'data_integrity': 0.2,
            'audit_trails': 0.15,
            'security': 0.1
        }
        
        # Get individual scores
        cfr_score = cfr_compliance.get('compliance_percentage', 0)
        iso_score = iso_compliance.get('compliance_percentage', 0)
        
        # Calculate data integrity score
        data_integrity_score = 100
        if data_integrity_checks:
            failed_checks = len([c for c in data_integrity_checks if c.status == 'failed'])
            warning_checks = len([c for c in data_integrity_checks if c.status == 'warning'])
            total_checks = len(data_integrity_checks)
            
            data_integrity_score = ((total_checks - failed_checks - (warning_checks * 0.5)) / total_checks) * 100
        
        audit_score = audit_validation.get('compliance_score', 0)
        security_score = security_compliance.get('compliance_score', 0)
        
        # Calculate weighted overall score
        overall_score = (
            cfr_score * weights['cfr_part11'] +
            iso_score * weights['iso13485'] +
            data_integrity_score * weights['data_integrity'] +
            audit_score * weights['audit_trails'] +
            security_score * weights['security']
        )
        
        return round(overall_score, 2)
    
    def _generate_compliance_recommendations(self, *args) -> List[str]:
        """Generate actionable compliance recommendations"""
        
        recommendations = []
        
        cfr_compliance, iso_compliance, data_integrity_checks, audit_validation, security_compliance = args
        
        # CFR Part 11 recommendations
        if cfr_compliance.get('compliance_percentage', 0) < 95:
            recommendations.append('Improve 21 CFR Part 11 compliance by enhancing electronic signature validation')
            recommendations.append('Implement stronger audit trail controls for electronic records')
        
        # ISO 13485 recommendations
        if iso_compliance.get('compliance_percentage', 0) < 90:
            recommendations.append('Enhance quality management system documentation and processes')
            recommendations.append('Improve nonconformity management and CAPA effectiveness')
        
        # Data integrity recommendations
        failed_integrity_checks = [c for c in data_integrity_checks if c.status == 'failed']
        if failed_integrity_checks:
            recommendations.append('Address critical data integrity issues identified in validation')
            recommendations.append('Implement automated data validation checks')
        
        # Audit trail recommendations
        if audit_validation.get('compliance_score', 0) < 85:
            recommendations.append('Improve audit trail completeness and integrity')
            recommendations.append('Implement automated audit trail monitoring')
        
        # Security recommendations
        if security_compliance.get('compliance_score', 0) < 90:
            recommendations.append('Enhance system security controls and access management')
            recommendations.append('Implement stronger authentication and authorization mechanisms')
        
        return recommendations
    
    def _identify_critical_issues(self, *args) -> List[str]:
        """Identify critical compliance issues requiring immediate attention"""
        
        critical_issues = []
        
        cfr_compliance, iso_compliance, data_integrity_checks, audit_validation, security_compliance = args
        
        # Critical CFR Part 11 issues
        if cfr_compliance.get('compliance_percentage', 0) < 80:
            critical_issues.append('CRITICAL: 21 CFR Part 11 compliance below acceptable threshold')
        
        # Critical data integrity issues
        critical_data_issues = [c for c in data_integrity_checks if c.status == 'failed' and c.details.get('severity') == 'high']
        if critical_data_issues:
            critical_issues.append(f'CRITICAL: {len(critical_data_issues)} high-severity data integrity issues detected')
        
        # Critical audit trail issues
        if audit_validation.get('compliance_score', 0) < 70:
            critical_issues.append('CRITICAL: Audit trail integrity below acceptable standards')
        
        # Critical security issues
        if security_compliance.get('compliance_score', 0) < 75:
            critical_issues.append('CRITICAL: Security compliance below minimum requirements')
        
        return critical_issues
    
    def _calculate_next_validation_date(self, overall_score: float, critical_issues: List[str]) -> datetime:
        """Calculate next validation due date based on compliance score and issues"""
        
        if critical_issues:
            # Critical issues require validation within 30 days
            return datetime.now() + timedelta(days=30)
        elif overall_score < 85:
            # Low compliance requires validation within 60 days
            return datetime.now() + timedelta(days=60)
        elif overall_score < 95:
            # Medium compliance requires validation within 90 days
            return datetime.now() + timedelta(days=90)
        else:
            # High compliance allows 180 days between validations
            return datetime.now() + timedelta(days=180)

# Factory function
def create_compliance_validation_service(db: Session) -> ComplianceValidationService:
    """Create and configure compliance validation service"""
    return ComplianceValidationService(db=db)