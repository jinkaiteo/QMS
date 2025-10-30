# Automated Compliance Service - Phase B Sprint 2 Day 4
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import json
import logging
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    WARNING = "warning"
    NON_COMPLIANT = "non_compliant"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ComplianceCheckType(Enum):
    """Types of compliance checks"""
    REAL_TIME = "real_time"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    ON_DEMAND = "on_demand"

@dataclass
class ComplianceRule:
    """Individual compliance rule definition"""
    rule_id: str
    rule_name: str
    description: str
    regulation: str  # CFR_PART_11, ISO_13485, FDA_QSR, etc.
    check_function: str
    parameters: Dict[str, Any]
    severity: str  # critical, high, medium, low
    frequency: str  # real_time, hourly, daily, weekly
    enabled: bool = True
    last_check: Optional[datetime] = None
    last_result: Optional[str] = None

@dataclass
class ComplianceResult:
    """Result of a compliance check"""
    rule_id: str
    check_timestamp: datetime
    status: ComplianceStatus
    score: float  # 0-100
    details: Dict[str, Any]
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    remediation_actions: List[Dict[str, Any]]
    next_check_due: datetime

@dataclass
class ComplianceScore:
    """Overall compliance scoring"""
    overall_score: float
    regulation_scores: Dict[str, float]
    module_scores: Dict[str, float]
    trend_direction: str  # improving, declining, stable
    last_updated: datetime
    score_history: List[Dict[str, Any]]

@dataclass
class ComplianceAlert:
    """Compliance alert notification"""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    rule_id: str
    triggered_at: datetime
    acknowledged: bool = False
    resolved: bool = False
    remediation_deadline: Optional[datetime] = None

class AutomatedComplianceService:
    """
    Automated Compliance Checking Service
    Real-time compliance monitoring, scoring, and alerting
    """
    
    def __init__(self, 
                 db: Session,
                 cfr_service=None,
                 iso_service=None,
                 fda_service=None,
                 validation_service=None):
        self.db = db
        self.cfr_service = cfr_service
        self.iso_service = iso_service
        self.fda_service = fda_service
        self.validation_service = validation_service
        
        # Load compliance rules
        self.compliance_rules = self._load_compliance_rules()
        
        # Compliance check registry
        self.check_functions = self._register_check_functions()
        
        # Scoring weights
        self.scoring_weights = self._load_scoring_weights()
        
        # Alert thresholds
        self.alert_thresholds = self._load_alert_thresholds()
        
    async def run_automated_compliance_check(self, 
                                           check_type: ComplianceCheckType = ComplianceCheckType.SCHEDULED,
                                           rule_ids: Optional[List[str]] = None) -> Dict[str, ComplianceResult]:
        """Run automated compliance checks"""
        
        logger.info(f"Starting automated compliance check: {check_type.value}")
        
        # Determine which rules to check
        rules_to_check = self._get_applicable_rules(check_type, rule_ids)
        
        # Run compliance checks concurrently
        check_tasks = []
        for rule in rules_to_check:
            if rule.enabled:
                task = self._execute_compliance_rule(rule)
                check_tasks.append((rule.rule_id, task))
        
        # Collect results
        compliance_results = {}
        
        for rule_id, task in check_tasks:
            try:
                result = await task
                compliance_results[rule_id] = result
                
                # Update rule's last check
                rule = next(r for r in self.compliance_rules if r.rule_id == rule_id)
                rule.last_check = datetime.now()
                rule.last_result = result.status.value
                
            except Exception as e:
                logger.error(f"Compliance check failed for rule {rule_id}: {str(e)}")
                compliance_results[rule_id] = self._create_error_result(rule_id, str(e))
        
        # Calculate overall compliance score
        overall_score = await self._calculate_compliance_score(compliance_results)
        
        # Store results
        await self._store_compliance_results(compliance_results, overall_score)
        
        # Process alerts and notifications
        await self._process_compliance_alerts(compliance_results, overall_score)
        
        logger.info(f"Automated compliance check completed: {len(compliance_results)} rules checked")
        
        return compliance_results
    
    async def get_real_time_compliance_score(self) -> ComplianceScore:
        """Get real-time compliance score with trending"""
        
        # Run quick compliance assessment
        quick_results = await self.run_automated_compliance_check(
            check_type=ComplianceCheckType.REAL_TIME
        )
        
        # Calculate scores by regulation and module
        regulation_scores = self._calculate_regulation_scores(quick_results)
        module_scores = self._calculate_module_scores(quick_results)
        
        # Get score history for trending
        score_history = await self._get_score_history(days=30)
        
        # Determine trend direction
        trend_direction = self._calculate_trend_direction(score_history)
        
        # Calculate overall score
        overall_score = self._calculate_weighted_overall_score(regulation_scores, module_scores)
        
        return ComplianceScore(
            overall_score=overall_score,
            regulation_scores=regulation_scores,
            module_scores=module_scores,
            trend_direction=trend_direction,
            last_updated=datetime.now(),
            score_history=score_history
        )
    
    async def trigger_event_driven_compliance_check(self, 
                                                  event_type: str,
                                                  event_data: Dict[str, Any]) -> List[ComplianceResult]:
        """Trigger compliance checks based on system events"""
        
        # Map events to compliance rules
        event_rule_mapping = {
            'document_created': ['cfr_part11_electronic_records', 'iso13485_document_control'],
            'document_signed': ['cfr_part11_signatures', 'cfr_part11_audit_trails'],
            'quality_event_created': ['iso13485_nonconformity_management', 'fda_adverse_event_reporting'],
            'training_completed': ['iso13485_training_effectiveness', 'training_compliance'],
            'user_login': ['security_access_controls', 'cfr_part11_audit_trails'],
            'data_modified': ['data_integrity_consistency', 'audit_trail_completeness'],
            'capa_created': ['capa_effectiveness', 'iso13485_nonconformity_management']
        }
        
        applicable_rules = event_rule_mapping.get(event_type, [])
        
        if not applicable_rules:
            logger.info(f"No compliance rules triggered for event type: {event_type}")
            return []
        
        # Run triggered compliance checks
        results = await self.run_automated_compliance_check(
            check_type=ComplianceCheckType.EVENT_DRIVEN,
            rule_ids=applicable_rules
        )
        
        # Log event-driven compliance check
        logger.info(f"Event-driven compliance check for {event_type}: {len(results)} rules checked")
        
        return list(results.values())
    
    def _load_compliance_rules(self) -> List[ComplianceRule]:
        """Load compliance rules configuration"""
        
        return [
            # CFR Part 11 Rules
            ComplianceRule(
                rule_id="cfr_part11_electronic_records",
                rule_name="21 CFR Part 11 Electronic Records",
                description="Validate electronic records integrity, attribution, and timestamps",
                regulation="CFR_PART_11",
                check_function="cfr_part11_electronic_records",
                parameters={"modules": ["edms", "qrm", "training"]},
                severity="critical",
                frequency="hourly"
            ),
            ComplianceRule(
                rule_id="cfr_part11_signatures",
                rule_name="21 CFR Part 11 Electronic Signatures",
                description="Validate electronic signature compliance and verification",
                regulation="CFR_PART_11",
                check_function="cfr_part11_signatures",
                parameters={"signature_algorithms": ["RSA", "ECDSA"]},
                severity="critical",
                frequency="hourly"
            ),
            ComplianceRule(
                rule_id="cfr_part11_audit_trails",
                rule_name="21 CFR Part 11 Audit Trails",
                description="Validate audit trail completeness and integrity",
                regulation="CFR_PART_11",
                check_function="cfr_part11_audit_trails",
                parameters={"retention_days": 2555},  # 7 years
                severity="critical",
                frequency="daily"
            ),
            
            # ISO 13485 Rules
            ComplianceRule(
                rule_id="iso13485_document_control",
                rule_name="ISO 13485 Document Control",
                description="Validate document control processes and effectiveness",
                regulation="ISO_13485",
                check_function="iso13485_document_control",
                parameters={"approval_required": True},
                severity="high",
                frequency="daily"
            ),
            ComplianceRule(
                rule_id="iso13485_training_effectiveness",
                rule_name="ISO 13485 Training Effectiveness",
                description="Validate training program effectiveness and compliance",
                regulation="ISO_13485",
                check_function="iso13485_training_effectiveness",
                parameters={"min_completion_rate": 90},
                severity="high",
                frequency="daily"
            ),
            ComplianceRule(
                rule_id="iso13485_nonconformity_management",
                rule_name="ISO 13485 Nonconformity Management",
                description="Validate nonconformity and CAPA management processes",
                regulation="ISO_13485",
                check_function="iso13485_nonconformity_management",
                parameters={"max_resolution_days": 30},
                severity="high",
                frequency="daily"
            ),
            
            # FDA Rules
            ComplianceRule(
                rule_id="fda_adverse_event_reporting",
                rule_name="FDA Adverse Event Reporting",
                description="Validate timely adverse event reporting compliance",
                regulation="FDA_QSR",
                check_function="fda_adverse_event_reporting",
                parameters={"reporting_deadline_hours": 24},
                severity="critical",
                frequency="real_time"
            ),
            ComplianceRule(
                rule_id="fda_device_tracking",
                rule_name="FDA Device Tracking",
                description="Validate device tracking and traceability compliance",
                regulation="FDA_QSR",
                check_function="fda_device_tracking",
                parameters={"tracking_required": True},
                severity="medium",
                frequency="weekly"
            ),
            
            # Data Integrity Rules
            ComplianceRule(
                rule_id="data_integrity_orphaned_records",
                rule_name="Data Integrity - Orphaned Records",
                description="Detect and report orphaned records in the system",
                regulation="DATA_INTEGRITY",
                check_function="data_integrity_orphaned_records",
                parameters={"check_all_tables": True},
                severity="medium",
                frequency="daily"
            ),
            ComplianceRule(
                rule_id="data_integrity_consistency",
                rule_name="Data Integrity - Consistency",
                description="Validate data consistency across related tables",
                regulation="DATA_INTEGRITY",
                check_function="data_integrity_consistency",
                parameters={"check_referential_integrity": True},
                severity="high",
                frequency="daily"
            ),
            
            # Operational Rules
            ComplianceRule(
                rule_id="training_compliance",
                rule_name="Training Compliance",
                description="Monitor training assignment completion and compliance",
                regulation="OPERATIONAL",
                check_function="training_compliance",
                parameters={"overdue_threshold_days": 7},
                severity="medium",
                frequency="daily"
            ),
            ComplianceRule(
                rule_id="quality_event_resolution",
                rule_name="Quality Event Resolution",
                description="Monitor quality event resolution timeliness",
                regulation="OPERATIONAL",
                check_function="quality_event_resolution",
                parameters={"max_resolution_days": 30},
                severity="high",
                frequency="daily"
            ),
            ComplianceRule(
                rule_id="capa_effectiveness",
                rule_name="CAPA Effectiveness",
                description="Monitor CAPA completion and effectiveness",
                regulation="OPERATIONAL",
                check_function="capa_effectiveness",
                parameters={"effectiveness_threshold": 80},
                severity="high",
                frequency="weekly"
            )
        ]
    
    def _register_check_functions(self) -> Dict[str, Callable]:
        """Register compliance check functions"""
        
        return {
            'cfr_part11_electronic_records': self._check_cfr_electronic_records,
            'cfr_part11_signatures': self._check_cfr_signatures,
            'cfr_part11_audit_trails': self._check_cfr_audit_trails,
            'iso13485_document_control': self._check_iso_document_control,
            'iso13485_training_effectiveness': self._check_iso_training_effectiveness,
            'iso13485_nonconformity_management': self._check_iso_nonconformity_management,
            'fda_adverse_event_reporting': self._check_fda_adverse_event_reporting,
            'fda_device_tracking': self._check_fda_device_tracking,
            'data_integrity_orphaned_records': self._check_data_integrity_orphaned,
            'data_integrity_consistency': self._check_data_integrity_consistency,
            'training_compliance': self._check_training_compliance,
            'quality_event_resolution': self._check_quality_event_resolution,
            'capa_effectiveness': self._check_capa_effectiveness
        }
    
    async def _check_cfr_electronic_records(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check CFR Part 11 electronic records compliance"""
        
        modules = parameters.get('modules', ['edms', 'qrm', 'training'])
        
        # Build dynamic query based on modules
        union_queries = []
        
        if 'edms' in modules:
            union_queries.append("""
                SELECT 'documents' as table_name, id, checksum, created_by, created_at, 
                       digital_signature, is_deleted
                FROM documents
            """)
        
        if 'qrm' in modules:
            union_queries.append("""
                SELECT 'quality_events' as table_name, id, checksum, created_by, created_at, 
                       signature_data as digital_signature, is_deleted
                FROM quality_events
            """)
        
        if 'training' in modules:
            union_queries.append("""
                SELECT 'training_programs' as table_name, id, checksum, created_by, created_at, 
                       NULL as digital_signature, is_deleted
                FROM training_programs
            """)
        
        if not union_queries:
            return {'compliance_percentage': 100, 'violations': [], 'details': 'No modules specified'}
        
        combined_query = f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN checksum IS NOT NULL THEN 1 END) as checksummed_records,
                COUNT(CASE WHEN created_by IS NOT NULL THEN 1 END) as attributed_records,
                COUNT(CASE WHEN created_at IS NOT NULL THEN 1 END) as timestamped_records,
                COUNT(CASE WHEN digital_signature IS NOT NULL THEN 1 END) as signed_records
            FROM (
                {' UNION ALL '.join(union_queries)}
            ) combined_records
            WHERE is_deleted = false
        """
        
        result = self.db.execute(text(combined_query))
        data = dict(zip(result.keys(), result.fetchone() or [0]*5))
        
        return self._process_electronic_records_result(data)
    
    def _process_electronic_records_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process electronic records compliance result"""
        
        total_records = data.get('total_records', 0)
        violations = []
        
        if total_records == 0:
            return {
                'compliance_percentage': 100,
                'violations': [],
                'details': 'No electronic records found'
            }
        
        # Calculate compliance percentages
        checksum_coverage = (data.get('checksummed_records', 0) / total_records) * 100
        attribution_coverage = (data.get('attributed_records', 0) / total_records) * 100
        timestamp_coverage = (data.get('timestamped_records', 0) / total_records) * 100
        
        # Check for violations
        if checksum_coverage < 95:
            violations.append({
                'type': 'insufficient_integrity_protection',
                'description': f'Only {checksum_coverage:.1f}% of records have integrity protection',
                'severity': 'high',
                'affected_records': total_records - data.get('checksummed_records', 0),
                'requirement': '21 CFR 11.10(a) - Record integrity protection'
            })
        
        if attribution_coverage < 98:
            violations.append({
                'type': 'insufficient_attribution',
                'description': f'Only {attribution_coverage:.1f}% of records have proper attribution',
                'severity': 'critical',
                'affected_records': total_records - data.get('attributed_records', 0),
                'requirement': '21 CFR 11.10(b) - Record attribution'
            })
        
        if timestamp_coverage < 99:
            violations.append({
                'type': 'insufficient_timestamps',
                'description': f'Only {timestamp_coverage:.1f}% of records have timestamps',
                'severity': 'medium',
                'affected_records': total_records - data.get('timestamped_records', 0),
                'requirement': '21 CFR 11.10(c) - Timestamp requirements'
            })
        
        # Calculate overall compliance
        compliance_percentage = (checksum_coverage + attribution_coverage + timestamp_coverage) / 3
        
        return {
            'compliance_percentage': round(compliance_percentage, 2),
            'violations': violations,
            'details': {
                'total_records': total_records,
                'checksum_coverage': round(checksum_coverage, 2),
                'attribution_coverage': round(attribution_coverage, 2),
                'timestamp_coverage': round(timestamp_coverage, 2),
                'signed_records': data.get('signed_records', 0)
            }
        }
    
    async def _check_training_compliance(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check training compliance"""
        
        overdue_threshold = parameters.get('overdue_threshold_days', 7)
        
        training_query = """
            SELECT 
                COUNT(*) as total_assignments,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_assignments,
                COUNT(CASE WHEN due_date < NOW() - INTERVAL '%s days' AND status != 'completed' THEN 1 END) as overdue_assignments,
                COUNT(CASE WHEN due_date <= NOW() + INTERVAL '7 days' AND status != 'completed' THEN 1 END) as due_soon_assignments,
                AVG(CASE WHEN status = 'completed' AND completed_at IS NOT NULL AND due_date IS NOT NULL 
                         THEN EXTRACT(EPOCH FROM (completed_at - due_date))/86400 
                    END) as avg_completion_delay_days
            FROM training_assignments 
            WHERE is_deleted = false
            AND created_at >= NOW() - INTERVAL '90 days'
        """ % overdue_threshold
        
        result = self.db.execute(text(training_query))
        data = dict(zip(result.keys(), result.fetchone() or [0]*5))
        
        return self._process_training_compliance_result(data, overdue_threshold)
    
    def _process_training_compliance_result(self, data: Dict[str, Any], overdue_threshold: int) -> Dict[str, Any]:
        """Process training compliance result"""
        
        total_assignments = data.get('total_assignments', 0)
        violations = []
        
        if total_assignments == 0:
            return {
                'compliance_percentage': 100,
                'violations': [],
                'details': 'No training assignments found'
            }
        
        # Calculate metrics
        completion_rate = (data.get('completed_assignments', 0) / total_assignments) * 100
        overdue_rate = (data.get('overdue_assignments', 0) / total_assignments) * 100
        avg_delay = data.get('avg_completion_delay_days', 0) or 0
        
        # Check for violations
        if completion_rate < 90:
            violations.append({
                'type': 'low_completion_rate',
                'description': f'Training completion rate is {completion_rate:.1f}% (target: 90%)',
                'severity': 'high',
                'affected_assignments': total_assignments - data.get('completed_assignments', 0),
                'requirement': 'Training effectiveness requirement'
            })
        
        if overdue_rate > 5:
            violations.append({
                'type': 'excessive_overdue_training',
                'description': f'{overdue_rate:.1f}% of training assignments are overdue',
                'severity': 'critical',
                'affected_assignments': data.get('overdue_assignments', 0),
                'requirement': 'Timely training completion requirement'
            })
        
        # Calculate compliance score
        compliance_score = max(0, 100 - (overdue_rate * 2) - max(0, (10 - (completion_rate - 90))))
        
        return {
            'compliance_percentage': round(compliance_score, 2),
            'violations': violations,
            'details': {
                'total_assignments': total_assignments,
                'completion_rate': round(completion_rate, 2),
                'overdue_rate': round(overdue_rate, 2),
                'due_soon': data.get('due_soon_assignments', 0),
                'avg_completion_delay_days': round(avg_delay, 1)
            }
        }
    
    def _calculate_compliance_score(self, results: Dict[str, ComplianceResult]) -> float:
        """Calculate overall compliance score"""
        
        if not results:
            return 0.0
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for rule_id, result in results.items():
            rule = next((r for r in self.compliance_rules if r.rule_id == rule_id), None)
            if rule:
                weight = self.scoring_weights.get(rule.severity, 1.0)
                total_weighted_score += result.score * weight
                total_weight += weight
        
        return round(total_weighted_score / max(total_weight, 1), 2)
    
    def _load_scoring_weights(self) -> Dict[str, float]:
        """Load scoring weights by severity"""
        
        return {
            'critical': 3.0,
            'high': 2.0,
            'medium': 1.5,
            'low': 1.0
        }
    
    def _load_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load alert thresholds"""
        
        return {
            'overall_score': {
                'critical': 70.0,
                'warning': 85.0
            },
            'regulation_score': {
                'critical': 75.0,
                'warning': 90.0
            },
            'individual_rule': {
                'critical': 60.0,
                'warning': 80.0
            }
        }
    
    def _create_error_result(self, rule_id: str, error_message: str) -> ComplianceResult:
        """Create error result for failed compliance check"""
        
        return ComplianceResult(
            rule_id=rule_id,
            check_timestamp=datetime.now(),
            status=ComplianceStatus.UNKNOWN,
            score=0.0,
            details={'error': error_message},
            violations=[],
            recommendations=[f"Fix compliance check error: {error_message}"],
            remediation_actions=[],
            next_check_due=datetime.now() + timedelta(hours=1)
        )

# Factory function
def create_automated_compliance_service(db: Session, **services) -> AutomatedComplianceService:
    """Create and configure automated compliance service"""
    return AutomatedComplianceService(db=db, **services)