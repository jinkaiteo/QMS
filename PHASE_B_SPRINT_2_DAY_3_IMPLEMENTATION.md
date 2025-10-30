# 🏛️ Phase B Sprint 2 Day 3 - Regulatory Framework & Advanced Dashboard Integration

**Phase**: B - Advanced Reporting & Analytics  
**Sprint**: 2 - Report Generation & Compliance  
**Day**: 3 - Regulatory Framework & Advanced Dashboard Integration  
**Focus**: Compliance reporting, regulatory templates, and advanced dashboard capabilities

---

## 🎯 **Day 3 Objectives**

### **Primary Goals:**
- [ ] Build 21 CFR Part 11 compliance reporting framework
- [ ] Implement ISO 13485 quality management system reports
- [ ] Create FDA audit trail and regulatory submission templates
- [ ] Develop compliance validation and data integrity verification
- [ ] Build advanced dashboard integration with Template Processing Pipeline
- [ ] Create regulatory compliance dashboard with real-time monitoring

### **Deliverables:**
- 21 CFR Part 11 electronic records and signatures reporting
- ISO 13485 compliance reporting templates
- FDA regulatory submission report generators
- Data integrity and audit trail validation services
- Advanced dashboard framework with regulatory widgets
- Real-time compliance monitoring dashboard

---

## 🏗️ **Building on Day 2 Foundation**

### **Existing Template Processing Infrastructure:**
- ✅ **Data Aggregation Pipeline**: Multi-source data collection with caching
- ✅ **Enhanced Chart Service**: Professional PDF and Excel chart generation
- ✅ **Template Validation Framework**: Comprehensive testing and error handling
- ✅ **Processing Orchestrator**: Job queue management and monitoring
- ✅ **Template Processing Service**: Unified end-to-end processing
- ✅ **REST API Integration**: 9 production-ready endpoints

### **Day 3 Regulatory Enhancements:**
- 🔜 **21 CFR Part 11 Framework**: Electronic records compliance
- 🔜 **ISO 13485 Templates**: Quality management reporting
- 🔜 **FDA Submission Tools**: Regulatory report generators
- 🔜 **Compliance Validation**: Data integrity verification
- 🔜 **Regulatory Dashboard**: Real-time compliance monitoring
- 🔜 **Advanced Integration**: Dashboard widgets with Template Processing

---

## 🏛️ **21 CFR Part 11 Compliance Framework**

### **Electronic Records and Signatures Reporting**

#### **CFR Part 11 Compliance Service**
```python
# backend/app/services/compliance/cfr_part11_service.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session

@dataclass
class ElectronicRecord:
    """21 CFR Part 11 Electronic Record"""
    record_id: str
    record_type: str
    creation_timestamp: datetime
    creator_user_id: int
    content_hash: str
    digital_signature: Optional[str]
    audit_trail: List[Dict[str, Any]]
    regulatory_status: str
    compliance_flags: Dict[str, bool]

@dataclass
class CFRComplianceReport:
    """21 CFR Part 11 Compliance Report"""
    report_id: str
    generation_timestamp: datetime
    compliance_period_start: datetime
    compliance_period_end: datetime
    electronic_records_summary: Dict[str, Any]
    signature_validation_results: Dict[str, Any]
    audit_trail_integrity: Dict[str, Any]
    non_compliance_issues: List[Dict[str, Any]]
    overall_compliance_score: float

class CFRPart11Service:
    """
    21 CFR Part 11 Compliance Service
    Electronic records, electronic signatures, and audit trails
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def generate_compliance_report(self, 
                                       start_date: datetime,
                                       end_date: datetime,
                                       report_scope: List[str]) -> CFRComplianceReport:
        """
        Generate comprehensive 21 CFR Part 11 compliance report
        
        Args:
            start_date: Report period start
            end_date: Report period end
            report_scope: Modules to include (edms, qrm, training, lims)
        """
        
        # Electronic Records Analysis
        electronic_records = await self._analyze_electronic_records(
            start_date, end_date, report_scope
        )
        
        # Digital Signature Validation
        signature_validation = await self._validate_digital_signatures(
            start_date, end_date, report_scope
        )
        
        # Audit Trail Integrity Check
        audit_trail_integrity = await self._verify_audit_trail_integrity(
            start_date, end_date, report_scope
        )
        
        # Compliance Issues Identification
        compliance_issues = await self._identify_compliance_issues(
            electronic_records, signature_validation, audit_trail_integrity
        )
        
        # Calculate overall compliance score
        compliance_score = self._calculate_compliance_score(
            electronic_records, signature_validation, audit_trail_integrity, compliance_issues
        )
        
        return CFRComplianceReport(
            report_id=f"cfr11_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generation_timestamp=datetime.now(),
            compliance_period_start=start_date,
            compliance_period_end=end_date,
            electronic_records_summary=electronic_records,
            signature_validation_results=signature_validation,
            audit_trail_integrity=audit_trail_integrity,
            non_compliance_issues=compliance_issues,
            overall_compliance_score=compliance_score
        )
    
    async def _analyze_electronic_records(self, 
                                        start_date: datetime, 
                                        end_date: datetime,
                                        report_scope: List[str]) -> Dict[str, Any]:
        """Analyze electronic records for compliance"""
        
        analysis = {
            'total_records': 0,
            'records_by_type': {},
            'records_by_module': {},
            'integrity_status': {},
            'signature_coverage': {},
            'compliance_flags': {}
        }
        
        # Analyze each module in scope
        for module in report_scope:
            if module == 'edms':
                edms_analysis = await self._analyze_edms_records(start_date, end_date)
                analysis['records_by_module']['edms'] = edms_analysis
                analysis['total_records'] += edms_analysis.get('count', 0)
                
            elif module == 'qrm':
                qrm_analysis = await self._analyze_qrm_records(start_date, end_date)
                analysis['records_by_module']['qrm'] = qrm_analysis
                analysis['total_records'] += qrm_analysis.get('count', 0)
                
            elif module == 'training':
                training_analysis = await self._analyze_training_records(start_date, end_date)
                analysis['records_by_module']['training'] = training_analysis
                analysis['total_records'] += training_analysis.get('count', 0)
                
            elif module == 'lims':
                lims_analysis = await self._analyze_lims_records(start_date, end_date)
                analysis['records_by_module']['lims'] = lims_analysis
                analysis['total_records'] += lims_analysis.get('count', 0)
        
        return analysis
    
    async def _validate_digital_signatures(self, 
                                         start_date: datetime, 
                                         end_date: datetime,
                                         report_scope: List[str]) -> Dict[str, Any]:
        """Validate digital signatures compliance"""
        
        from sqlalchemy import text
        
        # Query for signature validation
        signature_query = """
            SELECT 
                COUNT(*) as total_signatures,
                COUNT(CASE WHEN signature_valid = true THEN 1 END) as valid_signatures,
                COUNT(CASE WHEN signature_algorithm IS NOT NULL THEN 1 END) as algorithmic_signatures,
                COUNT(CASE WHEN signature_timestamp IS NOT NULL THEN 1 END) as timestamped_signatures,
                COUNT(CASE WHEN signer_certificate IS NOT NULL THEN 1 END) as certified_signatures
            FROM audit_logs al
            WHERE al.action IN ('create', 'update', 'approve', 'sign')
            AND al.created_at BETWEEN :start_date AND :end_date
            AND al.signature_data IS NOT NULL
        """
        
        result = self.db.execute(text(signature_query), {
            'start_date': start_date,
            'end_date': end_date
        })
        
        signature_data = dict(zip(result.keys(), result.fetchone() or [0]*5))
        
        # Calculate compliance percentages
        total = signature_data.get('total_signatures', 0)
        
        return {
            'total_signatures': total,
            'valid_signatures': signature_data.get('valid_signatures', 0),
            'validity_percentage': round((signature_data.get('valid_signatures', 0) / max(total, 1)) * 100, 2),
            'algorithmic_coverage': round((signature_data.get('algorithmic_signatures', 0) / max(total, 1)) * 100, 2),
            'timestamp_coverage': round((signature_data.get('timestamped_signatures', 0) / max(total, 1)) * 100, 2),
            'certificate_coverage': round((signature_data.get('certified_signatures', 0) / max(total, 1)) * 100, 2),
            'compliance_status': 'compliant' if signature_data.get('valid_signatures', 0) == total and total > 0 else 'non_compliant'
        }
    
    async def _verify_audit_trail_integrity(self, 
                                          start_date: datetime, 
                                          end_date: datetime,
                                          report_scope: List[str]) -> Dict[str, Any]:
        """Verify audit trail integrity for CFR compliance"""
        
        from sqlalchemy import text
        
        # Comprehensive audit trail analysis
        audit_query = """
            SELECT 
                COUNT(*) as total_audit_entries,
                COUNT(CASE WHEN checksum IS NOT NULL THEN 1 END) as checksummed_entries,
                COUNT(CASE WHEN user_id IS NOT NULL THEN 1 END) as user_attributed_entries,
                COUNT(CASE WHEN timestamp_verified = true THEN 1 END) as timestamp_verified_entries,
                COUNT(CASE WHEN data_integrity_hash IS NOT NULL THEN 1 END) as integrity_protected_entries,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT table_name) as tables_audited
            FROM audit_logs
            WHERE created_at BETWEEN :start_date AND :end_date
        """
        
        result = self.db.execute(text(audit_query), {
            'start_date': start_date,
            'end_date': end_date
        })
        
        audit_data = dict(zip(result.keys(), result.fetchone() or [0]*7))
        
        # Check for audit trail gaps
        gap_query = """
            WITH audit_sequence AS (
                SELECT 
                    id,
                    created_at,
                    LAG(created_at) OVER (ORDER BY created_at) as prev_timestamp,
                    EXTRACT(EPOCH FROM (created_at - LAG(created_at) OVER (ORDER BY created_at)))/60 as gap_minutes
                FROM audit_logs
                WHERE created_at BETWEEN :start_date AND :end_date
                ORDER BY created_at
            )
            SELECT 
                COUNT(*) as total_gaps,
                MAX(gap_minutes) as max_gap_minutes,
                AVG(gap_minutes) as avg_gap_minutes
            FROM audit_sequence
            WHERE gap_minutes > 60  -- Gaps longer than 1 hour
        """
        
        gap_result = self.db.execute(text(gap_query), {
            'start_date': start_date,
            'end_date': end_date
        })
        
        gap_data = dict(zip(gap_result.keys(), gap_result.fetchone() or [0, 0, 0]))
        
        total_entries = audit_data.get('total_audit_entries', 0)
        
        return {
            'total_entries': total_entries,
            'integrity_metrics': {
                'checksum_coverage': round((audit_data.get('checksummed_entries', 0) / max(total_entries, 1)) * 100, 2),
                'user_attribution': round((audit_data.get('user_attributed_entries', 0) / max(total_entries, 1)) * 100, 2),
                'timestamp_verification': round((audit_data.get('timestamp_verified_entries', 0) / max(total_entries, 1)) * 100, 2),
                'integrity_protection': round((audit_data.get('integrity_protected_entries', 0) / max(total_entries, 1)) * 100, 2)
            },
            'audit_coverage': {
                'unique_users': audit_data.get('unique_users', 0),
                'tables_audited': audit_data.get('tables_audited', 0)
            },
            'continuity_analysis': {
                'audit_gaps_detected': gap_data.get('total_gaps', 0),
                'max_gap_minutes': gap_data.get('max_gap_minutes', 0),
                'avg_gap_minutes': round(gap_data.get('avg_gap_minutes', 0), 2),
                'continuity_status': 'compliant' if gap_data.get('total_gaps', 0) == 0 else 'gaps_detected'
            }
        }
```

### **ISO 13485 Quality Management System Reporting**

#### **ISO 13485 Compliance Service**
```python
# backend/app/services/compliance/iso13485_service.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class ISO13485Report:
    """ISO 13485 Quality Management System Report"""
    report_id: str
    generation_timestamp: datetime
    reporting_period: Dict[str, datetime]
    quality_management_metrics: Dict[str, Any]
    document_control_analysis: Dict[str, Any]
    nonconformity_analysis: Dict[str, Any]
    corrective_preventive_actions: Dict[str, Any]
    management_review_data: Dict[str, Any]
    compliance_assessment: Dict[str, Any]

class ISO13485Service:
    """
    ISO 13485 Quality Management System Compliance Service
    Quality system effectiveness and regulatory compliance
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def generate_qms_report(self, 
                                start_date: datetime,
                                end_date: datetime) -> ISO13485Report:
        """
        Generate comprehensive ISO 13485 QMS compliance report
        """
        
        # Quality Management Metrics
        qm_metrics = await self._analyze_quality_management_metrics(start_date, end_date)
        
        # Document Control Analysis
        doc_control = await self._analyze_document_control(start_date, end_date)
        
        # Nonconformity Analysis
        nonconformity = await self._analyze_nonconformities(start_date, end_date)
        
        # CAPA Analysis
        capa_analysis = await self._analyze_corrective_preventive_actions(start_date, end_date)
        
        # Management Review Data
        mgmt_review = await self._prepare_management_review_data(start_date, end_date)
        
        # Overall Compliance Assessment
        compliance = await self._assess_iso13485_compliance(
            qm_metrics, doc_control, nonconformity, capa_analysis, mgmt_review
        )
        
        return ISO13485Report(
            report_id=f"iso13485_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generation_timestamp=datetime.now(),
            reporting_period={'start': start_date, 'end': end_date},
            quality_management_metrics=qm_metrics,
            document_control_analysis=doc_control,
            nonconformity_analysis=nonconformity,
            corrective_preventive_actions=capa_analysis,
            management_review_data=mgmt_review,
            compliance_assessment=compliance
        )
    
    async def _analyze_quality_management_metrics(self, 
                                                start_date: datetime, 
                                                end_date: datetime) -> Dict[str, Any]:
        """Analyze quality management system metrics"""
        
        from sqlalchemy import text
        
        # Quality metrics query
        metrics_query = """
            SELECT 
                -- Document Control Metrics
                (SELECT COUNT(*) FROM documents WHERE is_deleted = false) as total_documents,
                (SELECT COUNT(*) FROM documents WHERE status = 'approved' AND is_deleted = false) as approved_documents,
                (SELECT COUNT(*) FROM documents WHERE status = 'obsolete' AND is_deleted = false) as obsolete_documents,
                
                -- Training Effectiveness
                (SELECT COUNT(*) FROM training_assignments WHERE created_at BETWEEN :start_date AND :end_date) as training_assignments,
                (SELECT COUNT(*) FROM training_assignments WHERE status = 'completed' AND completed_at BETWEEN :start_date AND :end_date) as training_completed,
                
                -- Quality Events
                (SELECT COUNT(*) FROM quality_events WHERE created_at BETWEEN :start_date AND :end_date) as quality_events_total,
                (SELECT COUNT(*) FROM quality_events WHERE event_type = 'nonconformity' AND created_at BETWEEN :start_date AND :end_date) as nonconformities,
                (SELECT COUNT(*) FROM quality_events WHERE status = 'closed' AND resolved_at BETWEEN :start_date AND :end_date) as events_resolved,
                
                -- CAPA Effectiveness
                (SELECT COUNT(*) FROM capas WHERE created_at BETWEEN :start_date AND :end_date) as capas_initiated,
                (SELECT COUNT(*) FROM capas WHERE status = 'completed' AND completed_at BETWEEN :start_date AND :end_date) as capas_completed,
                
                -- Audit Results
                (SELECT COUNT(*) FROM audit_logs WHERE action = 'audit_finding' AND created_at BETWEEN :start_date AND :end_date) as audit_findings
        """
        
        result = self.db.execute(text(metrics_query), {
            'start_date': start_date,
            'end_date': end_date
        })
        
        metrics_data = dict(zip(result.keys(), result.fetchone() or [0]*11))
        
        # Calculate effectiveness percentages
        training_effectiveness = 0
        if metrics_data.get('training_assignments', 0) > 0:
            training_effectiveness = round(
                (metrics_data.get('training_completed', 0) / metrics_data.get('training_assignments', 1)) * 100, 2
            )
        
        event_resolution_rate = 0
        if metrics_data.get('quality_events_total', 0) > 0:
            event_resolution_rate = round(
                (metrics_data.get('events_resolved', 0) / metrics_data.get('quality_events_total', 1)) * 100, 2
            )
        
        capa_completion_rate = 0
        if metrics_data.get('capas_initiated', 0) > 0:
            capa_completion_rate = round(
                (metrics_data.get('capas_completed', 0) / metrics_data.get('capas_initiated', 1)) * 100, 2
            )
        
        return {
            'document_control': {
                'total_documents': metrics_data.get('total_documents', 0),
                'approved_documents': metrics_data.get('approved_documents', 0),
                'obsolete_documents': metrics_data.get('obsolete_documents', 0),
                'approval_rate': round((metrics_data.get('approved_documents', 0) / max(metrics_data.get('total_documents', 1), 1)) * 100, 2)
            },
            'training_effectiveness': {
                'assignments': metrics_data.get('training_assignments', 0),
                'completed': metrics_data.get('training_completed', 0),
                'effectiveness_rate': training_effectiveness
            },
            'quality_system_performance': {
                'total_events': metrics_data.get('quality_events_total', 0),
                'nonconformities': metrics_data.get('nonconformities', 0),
                'resolved_events': metrics_data.get('events_resolved', 0),
                'resolution_rate': event_resolution_rate
            },
            'capa_effectiveness': {
                'initiated': metrics_data.get('capas_initiated', 0),
                'completed': metrics_data.get('capas_completed', 0),
                'completion_rate': capa_completion_rate
            },
            'audit_performance': {
                'findings': metrics_data.get('audit_findings', 0)
            }
        }
```

I'll continue with the rest of the regulatory framework in the next iteration. Let me know if you'd like me to proceed with the complete implementation including the FDA templates, dashboard integration, and API endpoints.

Would you like me to continue with:
1. **Complete the regulatory framework** (FDA templates, compliance validation)
2. **Build the advanced dashboard integration** 
3. **Create the API endpoints for regulatory reporting**
4. **Move to a different focus area**

What's your preference for the next part of Day 3?