#!/usr/bin/env python3
# QMS Compliance Report Generator
# Generate compliance reports for audit and regulatory purposes

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.core.database import SessionLocal
from app.services.audit_service import AuditService
from app.models.audit import AuditAction


def generate_compliance_report(days_back: int = 30, output_file: str = "compliance-report.json"):
    """Generate a comprehensive compliance report."""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Initialize services
    audit_service = AuditService()
    
    print(f"Generating compliance report for {start_date.date()} to {end_date.date()}")
    
    # Generate report for each module
    modules = ["EDMS", "QRM", "TRM", "LIMS", "SYSTEM"]
    module_reports = {}
    
    for module in modules:
        print(f"Processing {module} module...")
        module_report = audit_service.generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            module=module
        )
        module_reports[module] = module_report
    
    # Generate overall report
    overall_report = audit_service.generate_compliance_report(
        start_date=start_date,
        end_date=end_date
    )
    
    # Compile comprehensive report
    compliance_report = {
        "generated_at": datetime.utcnow().isoformat(),
        "report_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days_back
        },
        "overall_summary": overall_report,
        "module_reports": module_reports,
        "compliance_assessment": {
            "cfr_21_part_11_compliant": all(
                report["compliance_status"] == "COMPLIANT" 
                for report in module_reports.values()
            ),
            "audit_trail_integrity": overall_report["integrity_check"]["integrity_percentage"],
            "data_quality_score": calculate_data_quality_score(module_reports),
            "recommendations": generate_recommendations(module_reports)
        }
    }
    
    # Save report
    with open(output_file, 'w') as f:
        json.dump(compliance_report, f, indent=2, default=str)
    
    print(f"Compliance report generated: {output_file}")
    
    # Print summary
    print("\n=== COMPLIANCE SUMMARY ===")
    print(f"21 CFR Part 11 Compliant: {compliance_report['compliance_assessment']['cfr_21_part_11_compliant']}")
    print(f"Audit Trail Integrity: {compliance_report['compliance_assessment']['audit_trail_integrity']:.1f}%")
    print(f"Data Quality Score: {compliance_report['compliance_assessment']['data_quality_score']:.1f}%")
    print(f"Total Activities: {overall_report['summary']['total_activities']}")
    print(f"Unique Users: {overall_report['summary']['unique_users']}")
    
    return compliance_report


def calculate_data_quality_score(module_reports):
    """Calculate overall data quality score."""
    if not module_reports:
        return 0.0
    
    total_activities = sum(
        report["summary"]["total_activities"] 
        for report in module_reports.values()
    )
    
    if total_activities == 0:
        return 100.0
    
    weighted_integrity = sum(
        report["integrity_check"]["integrity_percentage"] * report["summary"]["total_activities"]
        for report in module_reports.values()
    )
    
    return weighted_integrity / total_activities


def generate_recommendations(module_reports):
    """Generate compliance recommendations."""
    recommendations = []
    
    for module, report in module_reports.items():
        integrity_pct = report["integrity_check"]["integrity_percentage"]
        
        if integrity_pct < 100:
            recommendations.append(
                f"{module}: Address {report['integrity_check']['failed_records']} "
                f"failed integrity checks"
            )
        
        if report["summary"]["total_activities"] == 0:
            recommendations.append(
                f"{module}: No activity recorded - verify system usage"
            )
        
        if report["summary"]["unique_users"] < 2:
            recommendations.append(
                f"{module}: Limited user engagement - consider training"
            )
    
    if not recommendations:
        recommendations.append("No compliance issues identified - system operating within requirements")
    
    return recommendations


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate QMS compliance report")
    parser.add_argument(
        "--days", 
        type=int, 
        default=30, 
        help="Number of days to include in report (default: 30)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="compliance-report.json",
        help="Output file path (default: compliance-report.json)"
    )
    parser.add_argument(
        "--environment",
        type=str,
        default="development",
        help="Environment (development, staging, production)"
    )
    
    args = parser.parse_args()
    
    try:
        report = generate_compliance_report(
            days_back=args.days,
            output_file=args.output
        )
        
        # Exit with appropriate code
        if report["compliance_assessment"]["cfr_21_part_11_compliant"]:
            print("\n✅ System is compliant with 21 CFR Part 11 requirements")
            sys.exit(0)
        else:
            print("\n❌ Compliance issues detected - review recommendations")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error generating compliance report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()