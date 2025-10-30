# Regulatory Template Library - Phase B Sprint 2 Day 4
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class RegulatoryTemplate:
    """Pre-built regulatory report template"""
    template_id: str
    template_name: str
    regulation_type: str  # CFR_PART_11, ISO_13485, FDA_QSR, etc.
    audit_type: str  # internal, external, regulatory, compliance
    description: str
    template_config: Dict[str, Any]
    data_sources: List[Dict[str, Any]]
    required_sections: List[str]
    optional_sections: List[str]
    compliance_criteria: Dict[str, Any]
    generation_parameters: Dict[str, Any]
    last_updated: datetime
    version: str = "1.0"
    audit_ready: bool = True

@dataclass
class TemplateGenerationResult:
    """Result of regulatory template generation"""
    template_id: str
    generated_at: datetime
    output_files: List[str]
    compliance_score: float
    audit_findings: List[Dict[str, Any]]
    recommendations: List[str]
    generation_time_ms: int
    validation_passed: bool

class RegulatoryTemplateLibrary:
    """
    Pre-built Regulatory Template Library
    Audit-ready templates for compliance reporting and regulatory submissions
    """
    
    def __init__(self, 
                 db: Session,
                 template_processing_service=None,
                 compliance_service=None):
        self.db = db
        self.template_processing_service = template_processing_service
        self.compliance_service = compliance_service
        
        # Load pre-built templates
        self.regulatory_templates = self._load_regulatory_templates()
        
    def get_available_templates(self, 
                              regulation_type: Optional[str] = None,
                              audit_type: Optional[str] = None) -> List[RegulatoryTemplate]:
        """Get available regulatory templates"""
        
        templates = self.regulatory_templates.copy()
        
        if regulation_type:
            templates = [t for t in templates if t.regulation_type == regulation_type]
        
        if audit_type:
            templates = [t for t in templates if t.audit_type == audit_type]
        
        return templates
    
    async def generate_regulatory_report(self, 
                                       template_id: str,
                                       parameters: Dict[str, Any]) -> TemplateGenerationResult:
        """Generate regulatory report from pre-built template"""
        
        start_time = datetime.now()
        
        # Get template
        template = self._get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        logger.info(f"Generating regulatory report from template: {template.template_name}")
        
        # Validate parameters against template requirements
        validation_result = self._validate_template_parameters(template, parameters)
        if not validation_result['valid']:
            raise ValueError(f"Parameter validation failed: {validation_result['errors']}")
        
        # Merge template parameters with user parameters
        final_parameters = {**template.generation_parameters, **parameters}
        
        # Generate report using Template Processing Service
        if self.template_processing_service:
            from ..reporting.template_processing_service import TemplateProcessingRequest
            
            processing_request = TemplateProcessingRequest(
                template_id=self._get_template_processing_id(template),
                parameters=final_parameters,
                output_format=parameters.get('output_format', 'both'),
                validate_template=True,
                generate_charts=True,
                cache_results=False  # Don't cache regulatory reports
            )
            
            processing_result = await self.template_processing_service.process_template(processing_request)
            
            if not processing_result.success:
                raise Exception(f"Template processing failed: {processing_result.error_message}")
            
            # Perform regulatory-specific validation
            compliance_score, audit_findings = await self._validate_regulatory_compliance(
                template, processing_result, final_parameters
            )
            
            # Generate recommendations
            recommendations = self._generate_regulatory_recommendations(
                template, audit_findings, compliance_score
            )
            
            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return TemplateGenerationResult(
                template_id=template_id,
                generated_at=datetime.now(),
                output_files=processing_result.generated_files,
                compliance_score=compliance_score,
                audit_findings=audit_findings,
                recommendations=recommendations,
                generation_time_ms=generation_time,
                validation_passed=compliance_score >= template.compliance_criteria.get('min_score', 80)
            )
        
        else:
            # Fallback generation without Template Processing Service
            return await self._generate_simple_regulatory_report(template, final_parameters, start_time)
    
    def _load_regulatory_templates(self) -> List[RegulatoryTemplate]:
        """Load pre-built regulatory templates"""
        
        templates = []
        
        # CFR Part 11 Compliance Audit Template
        templates.append(RegulatoryTemplate(
            template_id="cfr_part11_compliance_audit",
            template_name="21 CFR Part 11 Compliance Audit Report",
            regulation_type="CFR_PART_11",
            audit_type="compliance",
            description="Comprehensive 21 CFR Part 11 compliance audit report for electronic records and signatures",
            template_config={
                "report_type": "both",
                "layout": {
                    "orientation": "portrait",
                    "margins": {"top": 25, "bottom": 25, "left": 20, "right": 20}
                },
                "styling": {
                    "colors": {
                        "primary": "#1976d2",
                        "compliance": "#4caf50",
                        "warning": "#ff9800",
                        "critical": "#f44336"
                    },
                    "fonts": {
                        "heading": {"family": "Arial", "size": 16, "bold": True},
                        "body": {"family": "Arial", "size": 11},
                        "footer": {"family": "Arial", "size": 9}
                    }
                },
                "charts": [
                    {
                        "id": "compliance_overview",
                        "type": "gauge",
                        "title": "Overall CFR Part 11 Compliance Score",
                        "data_source": "cfr_compliance_data",
                        "width": 400,
                        "height": 300
                    },
                    {
                        "id": "electronic_records_analysis",
                        "type": "bar",
                        "title": "Electronic Records Compliance Analysis",
                        "data_source": "electronic_records_data",
                        "width": 600,
                        "height": 400
                    },
                    {
                        "id": "signature_validation",
                        "type": "pie",
                        "title": "Electronic Signature Validation Results",
                        "data_source": "signature_validation_data",
                        "width": 500,
                        "height": 400
                    }
                ]
            },
            data_sources=[
                {
                    "name": "cfr_compliance_data",
                    "endpoint": "/api/v1/analytics/compliance/cfr-part11/report",
                    "method": "POST",
                    "required": True,
                    "cache_ttl": 0  # No caching for regulatory reports
                },
                {
                    "name": "electronic_records_data",
                    "endpoint": "db:cfr_electronic_records_analysis",
                    "required": True
                },
                {
                    "name": "signature_validation_data",
                    "endpoint": "db:cfr_signature_validation",
                    "required": True
                },
                {
                    "name": "audit_trail_data",
                    "endpoint": "db:cfr_audit_trail_integrity",
                    "required": True
                }
            ],
            required_sections=[
                "executive_summary",
                "compliance_overview",
                "electronic_records_analysis",
                "signature_validation",
                "audit_trail_review",
                "findings_and_observations",
                "recommendations",
                "compliance_certification"
            ],
            optional_sections=[
                "detailed_methodology",
                "risk_assessment",
                "remediation_plan",
                "appendices"
            ],
            compliance_criteria={
                "min_score": 85.0,
                "required_controls": [
                    "electronic_record_integrity",
                    "signature_verification",
                    "audit_trail_completeness",
                    "access_controls"
                ],
                "critical_findings_threshold": 0
            },
            generation_parameters={
                "audit_period_days": 90,
                "include_risk_assessment": True,
                "detailed_findings": True,
                "include_remediation_plan": True
            },
            last_updated=datetime.now()
        ))
        
        # ISO 13485 QMS Audit Template
        templates.append(RegulatoryTemplate(
            template_id="iso13485_qms_audit",
            template_name="ISO 13485 Quality Management System Audit Report",
            regulation_type="ISO_13485",
            audit_type="internal",
            description="Comprehensive ISO 13485 QMS internal audit report",
            template_config={
                "report_type": "both",
                "layout": {
                    "orientation": "portrait",
                    "margins": {"top": 25, "bottom": 25, "left": 20, "right": 20}
                },
                "charts": [
                    {
                        "id": "qms_effectiveness",
                        "type": "radar",
                        "title": "QMS Effectiveness Assessment",
                        "data_source": "qms_metrics_data",
                        "width": 500,
                        "height": 400
                    },
                    {
                        "id": "nonconformity_trends",
                        "type": "line",
                        "title": "Nonconformity Trends",
                        "data_source": "nonconformity_data",
                        "width": 600,
                        "height": 400
                    },
                    {
                        "id": "capa_effectiveness",
                        "type": "bar",
                        "title": "CAPA Effectiveness Metrics",
                        "data_source": "capa_data",
                        "width": 600,
                        "height": 400
                    }
                ]
            },
            data_sources=[
                {
                    "name": "qms_metrics_data",
                    "endpoint": "/api/v1/analytics/compliance/iso13485/report",
                    "method": "POST",
                    "required": True
                },
                {
                    "name": "nonconformity_data",
                    "endpoint": "db:iso_nonconformity_analysis",
                    "required": True
                },
                {
                    "name": "capa_data",
                    "endpoint": "db:iso_capa_effectiveness",
                    "required": True
                },
                {
                    "name": "training_effectiveness_data",
                    "endpoint": "db:iso_training_effectiveness",
                    "required": True
                }
            ],
            required_sections=[
                "audit_summary",
                "qms_effectiveness_assessment",
                "document_control_review",
                "training_effectiveness",
                "nonconformity_management",
                "capa_review",
                "audit_findings",
                "improvement_opportunities",
                "management_review_input"
            ],
            optional_sections=[
                "process_maps",
                "risk_analysis",
                "customer_feedback_analysis",
                "supplier_performance"
            ],
            compliance_criteria={
                "min_score": 80.0,
                "required_processes": [
                    "document_control",
                    "training_management",
                    "nonconformity_control",
                    "corrective_preventive_action"
                ]
            },
            generation_parameters={
                "audit_scope": "full_qms",
                "include_process_effectiveness": True,
                "risk_based_approach": True
            },
            last_updated=datetime.now()
        ))
        
        # FDA 510(k) Submission Template
        templates.append(RegulatoryTemplate(
            template_id="fda_510k_submission",
            template_name="FDA 510(k) Premarket Notification Submission",
            regulation_type="FDA_QSR",
            audit_type="regulatory",
            description="Complete FDA 510(k) submission package generation",
            template_config={
                "report_type": "pdf",
                "layout": {
                    "orientation": "portrait",
                    "margins": {"top": 25, "bottom": 25, "left": 20, "right": 20}
                },
                "charts": [
                    {
                        "id": "predicate_comparison",
                        "type": "table",
                        "title": "Predicate Device Comparison Matrix",
                        "data_source": "predicate_analysis_data",
                        "width": 700,
                        "height": 500
                    },
                    {
                        "id": "performance_data",
                        "type": "bar",
                        "title": "Device Performance Data Summary",
                        "data_source": "performance_data",
                        "width": 600,
                        "height": 400
                    }
                ]
            },
            data_sources=[
                {
                    "name": "device_information",
                    "endpoint": "/api/v1/analytics/compliance/fda/submission",
                    "method": "POST",
                    "required": True
                },
                {
                    "name": "predicate_analysis_data",
                    "endpoint": "db:fda_predicate_analysis",
                    "required": True
                },
                {
                    "name": "performance_data",
                    "endpoint": "db:device_performance_data",
                    "required": True
                }
            ],
            required_sections=[
                "cover_letter",
                "device_description",
                "intended_use",
                "predicate_device_information",
                "substantial_equivalence_comparison",
                "performance_data",
                "labeling",
                "risk_analysis",
                "conclusion"
            ],
            optional_sections=[
                "clinical_data",
                "biocompatibility_data",
                "software_documentation",
                "sterilization_validation"
            ],
            compliance_criteria={
                "min_score": 95.0,
                "required_documentation": [
                    "device_description",
                    "predicate_comparison",
                    "substantial_equivalence",
                    "performance_testing"
                ]
            },
            generation_parameters={
                "submission_type": "510k",
                "include_predicate_analysis": True,
                "detailed_comparison": True
            },
            last_updated=datetime.now()
        ))
        
        # FDA Annual Report Template
        templates.append(RegulatoryTemplate(
            template_id="fda_annual_report",
            template_name="FDA Annual Report",
            regulation_type="FDA_QSR",
            audit_type="regulatory",
            description="FDA Annual Report for medical device compliance",
            template_config={
                "report_type": "both",
                "charts": [
                    {
                        "id": "adverse_events_summary",
                        "type": "pie",
                        "title": "Adverse Events Summary",
                        "data_source": "adverse_events_data",
                        "width": 500,
                        "height": 400
                    },
                    {
                        "id": "quality_trends",
                        "type": "line",
                        "title": "Quality Metrics Trends",
                        "data_source": "quality_trends_data",
                        "width": 600,
                        "height": 400
                    }
                ]
            },
            data_sources=[
                {
                    "name": "annual_summary_data",
                    "endpoint": "/api/v1/analytics/compliance/fda/submission",
                    "method": "POST",
                    "required": True
                },
                {
                    "name": "adverse_events_data",
                    "endpoint": "db:fda_adverse_events_annual",
                    "required": True
                },
                {
                    "name": "quality_trends_data",
                    "endpoint": "db:annual_quality_trends",
                    "required": True
                }
            ],
            required_sections=[
                "executive_summary",
                "adverse_events_summary",
                "quality_system_changes",
                "manufacturing_changes",
                "labeling_changes",
                "regulatory_correspondence",
                "compliance_status"
            ],
            optional_sections=[
                "risk_management_updates",
                "post_market_surveillance",
                "clinical_data_updates"
            ],
            compliance_criteria={
                "min_score": 90.0,
                "required_reporting": [
                    "adverse_events",
                    "device_modifications",
                    "quality_changes"
                ]
            },
            generation_parameters={
                "reporting_year": datetime.now().year - 1,
                "include_trends": True,
                "detailed_analysis": True
            },
            last_updated=datetime.now()
        ))
        
        # Data Integrity Assessment Template
        templates.append(RegulatoryTemplate(
            template_id="data_integrity_assessment",
            template_name="Data Integrity Assessment Report",
            regulation_type="DATA_INTEGRITY",
            audit_type="compliance",
            description="Comprehensive data integrity assessment across all QMS modules",
            template_config={
                "report_type": "both",
                "charts": [
                    {
                        "id": "integrity_score_overview",
                        "type": "gauge",
                        "title": "Overall Data Integrity Score",
                        "data_source": "integrity_overview_data",
                        "width": 400,
                        "height": 300
                    },
                    {
                        "id": "integrity_by_module",
                        "type": "bar",
                        "title": "Data Integrity by Module",
                        "data_source": "module_integrity_data",
                        "width": 600,
                        "height": 400
                    },
                    {
                        "id": "validation_results",
                        "type": "table",
                        "title": "Validation Check Results",
                        "data_source": "validation_results_data",
                        "width": 700,
                        "height": 500
                    }
                ]
            },
            data_sources=[
                {
                    "name": "integrity_overview_data",
                    "endpoint": "/api/v1/analytics/compliance/validation",
                    "method": "POST",
                    "required": True
                },
                {
                    "name": "module_integrity_data",
                    "endpoint": "db:data_integrity_by_module",
                    "required": True
                },
                {
                    "name": "validation_results_data",
                    "endpoint": "db:integrity_validation_results",
                    "required": True
                }
            ],
            required_sections=[
                "assessment_summary",
                "data_integrity_overview",
                "module_analysis",
                "validation_results",
                "gap_analysis",
                "remediation_recommendations",
                "action_plan"
            ],
            optional_sections=[
                "methodology",
                "risk_assessment",
                "compliance_matrix",
                "validation_evidence"
            ],
            compliance_criteria={
                "min_score": 85.0,
                "critical_checks": [
                    "orphaned_records",
                    "data_consistency",
                    "referential_integrity",
                    "audit_completeness"
                ]
            },
            generation_parameters={
                "assessment_scope": "all_modules",
                "include_remediation": True,
                "detailed_analysis": True
            },
            last_updated=datetime.now()
        ))
        
        return templates
    
    def _get_template(self, template_id: str) -> Optional[RegulatoryTemplate]:
        """Get template by ID"""
        return next((t for t in self.regulatory_templates if t.template_id == template_id), None)
    
    def _validate_template_parameters(self, template: RegulatoryTemplate, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters against template requirements"""
        
        errors = []
        warnings = []
        
        # Check required parameters based on template type
        if template.regulation_type == "CFR_PART_11":
            required_params = ['start_date', 'end_date', 'report_scope']
        elif template.regulation_type == "ISO_13485":
            required_params = ['start_date', 'end_date']
        elif template.regulation_type == "FDA_QSR":
            if "510k" in template.template_id:
                required_params = ['device_id', 'submission_parameters']
            elif "annual" in template.template_id:
                required_params = ['reporting_year', 'device_scope']
            else:
                required_params = []
        else:
            required_params = []
        
        for param in required_params:
            if param not in parameters:
                errors.append(f"Required parameter '{param}' is missing")
        
        # Validate date parameters
        if 'start_date' in parameters and 'end_date' in parameters:
            try:
                start_date = datetime.fromisoformat(parameters['start_date'].replace('Z', '+00:00')) if isinstance(parameters['start_date'], str) else parameters['start_date']
                end_date = datetime.fromisoformat(parameters['end_date'].replace('Z', '+00:00')) if isinstance(parameters['end_date'], str) else parameters['end_date']
                
                if start_date >= end_date:
                    errors.append("Start date must be before end date")
                
                if (end_date - start_date).days > 365:
                    warnings.append("Report period exceeds 1 year, consider shorter periods for accuracy")
                    
            except (ValueError, TypeError) as e:
                errors.append(f"Invalid date format: {str(e)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    async def _validate_regulatory_compliance(self, 
                                            template: RegulatoryTemplate,
                                            processing_result: Any,
                                            parameters: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
        """Validate regulatory compliance of generated report"""
        
        compliance_score = 100.0
        audit_findings = []
        
        # Check if all required sections are present
        if template.required_sections:
            missing_sections = []
            # This would check the generated report content
            # For now, we'll simulate the check
            for section in template.required_sections:
                # Simulate section presence check
                if section not in processing_result.metadata.get('sections_generated', []):
                    missing_sections.append(section)
            
            if missing_sections:
                compliance_score -= len(missing_sections) * 5
                audit_findings.append({
                    'finding_type': 'missing_required_sections',
                    'severity': 'critical',
                    'description': f"Missing required sections: {', '.join(missing_sections)}",
                    'sections': missing_sections
                })
        
        # Check data completeness
        if processing_result.aggregation_result:
            failed_sources = processing_result.aggregation_result.sources_failed
            if failed_sources:
                compliance_score -= len(failed_sources) * 10
                audit_findings.append({
                    'finding_type': 'incomplete_data_collection',
                    'severity': 'high',
                    'description': f"Failed to collect data from: {', '.join(failed_sources)}",
                    'failed_sources': failed_sources
                })
        
        # Check chart generation
        if processing_result.chart_results:
            failed_charts = [r for r in processing_result.chart_results if not r.success]
            if failed_charts:
                compliance_score -= len(failed_charts) * 3
                audit_findings.append({
                    'finding_type': 'chart_generation_failures',
                    'severity': 'medium',
                    'description': f"{len(failed_charts)} charts failed to generate",
                    'failed_charts': [c.chart_id for c in failed_charts]
                })
        
        # Validate against compliance criteria
        min_score = template.compliance_criteria.get('min_score', 80)
        if compliance_score < min_score:
            audit_findings.append({
                'finding_type': 'compliance_score_below_threshold',
                'severity': 'critical',
                'description': f"Compliance score {compliance_score:.1f}% below minimum {min_score}%",
                'threshold': min_score,
                'actual_score': compliance_score
            })
        
        return max(0, compliance_score), audit_findings
    
    def _generate_regulatory_recommendations(self, 
                                           template: RegulatoryTemplate,
                                           audit_findings: List[Dict[str, Any]],
                                           compliance_score: float) -> List[str]:
        """Generate regulatory recommendations"""
        
        recommendations = []
        
        if compliance_score < 90:
            recommendations.append("Conduct thorough review of data collection processes to improve compliance score")
        
        for finding in audit_findings:
            if finding['finding_type'] == 'missing_required_sections':
                recommendations.append(f"Ensure all required sections are included: {', '.join(finding['sections'])}")
            elif finding['finding_type'] == 'incomplete_data_collection':
                recommendations.append("Investigate and resolve data source connectivity issues")
            elif finding['finding_type'] == 'chart_generation_failures':
                recommendations.append("Review chart configurations and data formats for failed visualizations")
        
        # Template-specific recommendations
        if template.regulation_type == "CFR_PART_11":
            recommendations.append("Verify electronic signature compliance and audit trail integrity")
        elif template.regulation_type == "ISO_13485":
            recommendations.append("Ensure QMS process effectiveness metrics meet organizational targets")
        elif template.regulation_type == "FDA_QSR":
            recommendations.append("Confirm all FDA regulatory requirements are addressed in submission")
        
        return recommendations
    
    def _get_template_processing_id(self, template: RegulatoryTemplate) -> int:
        """Get template processing ID (would be stored in database)"""
        # For now, return a simulated ID based on template
        template_mapping = {
            "cfr_part11_compliance_audit": 1001,
            "iso13485_qms_audit": 1002,
            "fda_510k_submission": 1003,
            "fda_annual_report": 1004,
            "data_integrity_assessment": 1005
        }
        return template_mapping.get(template.template_id, 1000)

# Factory function
def create_regulatory_template_library(db: Session, **services) -> RegulatoryTemplateLibrary:
    """Create and configure regulatory template library"""
    return RegulatoryTemplateLibrary(db=db, **services)