# CFR Part 11 Service Implementation - Phase B Sprint 2 Day 3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session

# Re-export from the compliance validation service for now
from .compliance_validation_service import ComplianceValidationService

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
        self.validation_service = ComplianceValidationService(db)
        
    async def generate_compliance_report(self, 
                                       start_date: datetime,
                                       end_date: datetime,
                                       report_scope: List[str]) -> CFRComplianceReport:
        """Generate comprehensive 21 CFR Part 11 compliance report"""
        
        # Use the validation service for the actual implementation
        validation_result = await self.validation_service.perform_comprehensive_validation(
            validation_scope=report_scope,
            include_data_integrity=True,
            include_audit_validation=True
        )
        
        return CFRComplianceReport(
            report_id=f"cfr11_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generation_timestamp=datetime.now(),
            compliance_period_start=start_date,
            compliance_period_end=end_date,
            electronic_records_summary=validation_result.cfr_part11_compliance.get('electronic_records', {}),
            signature_validation_results=validation_result.cfr_part11_compliance.get('electronic_signatures', {}),
            audit_trail_integrity=validation_result.cfr_part11_compliance.get('audit_trails', {}),
            non_compliance_issues=[{'issue': issue} for issue in validation_result.critical_issues],
            overall_compliance_score=validation_result.cfr_part11_compliance.get('compliance_percentage', 0)
        )

def create_cfr_part11_service(db: Session) -> CFRPart11Service:
    """Create and configure CFR Part 11 service"""
    return CFRPart11Service(db=db)