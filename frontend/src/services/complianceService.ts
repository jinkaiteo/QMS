// Compliance Service - Phase C Frontend Development Continuation
import { apiClient } from './apiClient';

export interface ComplianceAssessment {
  assessment_id: string;
  overall_score: number;
  module_scores: Record<string, number>;
  critical_issues: string[];
  warnings: string[];
  recommendations: string[];
  audit_readiness: string;
  compliance_gaps: Array<Record<string, any>>;
  next_review_date: string;
  generated_at: string;
}

export interface ValidationRule {
  rule_id: string;
  rule_name: string;
  description: string;
  regulation: string;
  severity: string;
  module: string;
  is_active: boolean;
  automated: boolean;
  check_frequency: string;
}

export interface ComplianceReport {
  report_id: string;
  report_type: string;
  regulation: string;
  period_start: string;
  period_end: string;
  findings: Array<Record<string, any>>;
  recommendations: string[];
  status: string;
  generated_by: string;
  generated_at: string;
}

export interface DataIntegrityCheck {
  check_id: string;
  check_type: string;
  entity_type: string;
  entity_id: number;
  status: string;
  findings: string[];
  severity: string;
  remediation_required: boolean;
  checked_at: string;
}

export interface AuditTrailEntry {
  entry_id: string;
  user_id: number;
  module: string;
  action: string;
  entity_type: string;
  entity_id: number;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  timestamp: string;
  ip_address: string;
  user_agent: string;
}

export interface CFRPart11Status {
  regulation: string;
  overall_compliance: number;
  electronic_records: Record<string, any>;
  electronic_signatures: Record<string, any>;
  audit_trail: Record<string, any>;
  access_controls: Record<string, any>;
  data_integrity: Record<string, any>;
  findings: string[];
  recommendations: string[];
  last_assessment: string;
}

export interface ISO13485Status {
  regulation: string;
  overall_compliance: number;
  quality_management: Record<string, any>;
  document_control: Record<string, any>;
  management_responsibility: Record<string, any>;
  resource_management: Record<string, any>;
  product_realization: Record<string, any>;
  measurement_analysis: Record<string, any>;
  improvement: Record<string, any>;
  findings: string[];
  recommendations: string[];
  certification_status: string;
}

export interface ComplianceDashboard {
  timeframe: string;
  generated_at: string;
  overall_compliance: number;
  regulation_status: Record<string, any>;
  module_compliance: Record<string, any>;
  recent_assessments: Array<Record<string, any>>;
  critical_issues: string[];
  upcoming_deadlines: Array<Record<string, any>>;
  automation_status: Record<string, any>;
  trends: Record<string, any>;
  recommendations: string[];
}

class ComplianceService {
  private baseURL = '/api/v1/compliance';

  async getComplianceAssessment(
    modules: string[],
    regulation: string = 'all',
    detailed: boolean = true
  ): Promise<ComplianceAssessment> {
    const response = await apiClient.get(`${this.baseURL}/assessment`, {
      params: {
        modules,
        regulation,
        detailed
      }
    });
    return response.data;
  }

  async getValidationRules(
    regulation?: string,
    module?: string,
    activeOnly: boolean = true
  ): Promise<ValidationRule[]> {
    const response = await apiClient.get(`${this.baseURL}/validation-rules`, {
      params: {
        regulation,
        module,
        active_only: activeOnly
      }
    });
    return response.data;
  }

  async runComplianceValidation(
    modules: string[],
    rules?: string[]
  ): Promise<{ success: boolean; validation_id: string; message: string }> {
    const response = await apiClient.post(`${this.baseURL}/validate`, null, {
      params: {
        modules,
        rules
      }
    });
    return response.data;
  }

  async getCFRPart11Status(module?: string): Promise<CFRPart11Status> {
    const response = await apiClient.get(`${this.baseURL}/cfr-part11-status`, {
      params: { module }
    });
    return response.data;
  }

  async getISO13485Status(processes?: string[]): Promise<ISO13485Status> {
    const response = await apiClient.get(`${this.baseURL}/iso13485-status`, {
      params: { processes }
    });
    return response.data;
  }

  async runDataIntegrityCheck(
    entityType: string,
    entityIds?: number[],
    checkType: string = 'comprehensive'
  ): Promise<{
    check_id: string;
    results: DataIntegrityCheck[];
    summary: Record<string, number>;
  }> {
    const response = await apiClient.get(`${this.baseURL}/data-integrity-check`, {
      params: {
        entity_type: entityType,
        entity_ids: entityIds,
        check_type: checkType
      }
    });
    return response.data;
  }

  async getAuditTrail(
    module?: string,
    userId?: number,
    entityType?: string,
    startDate?: string,
    endDate?: string,
    limit: number = 100
  ): Promise<{
    filters: Record<string, any>;
    total_entries: number;
    entries: AuditTrailEntry[];
  }> {
    const response = await apiClient.get(`${this.baseURL}/audit-trail`, {
      params: {
        module,
        user_id: userId,
        entity_type: entityType,
        start_date: startDate,
        end_date: endDate,
        limit
      }
    });
    return response.data;
  }

  async generateComplianceReport(
    reportType: string,
    regulation: string,
    modules: string[],
    periodStart: string,
    periodEnd: string,
    format: string = 'pdf'
  ): Promise<{ success: boolean; report_id: string; message: string }> {
    const response = await apiClient.post(`${this.baseURL}/generate-report`, null, {
      params: {
        report_type: reportType,
        regulation,
        modules,
        period_start: periodStart,
        period_end: periodEnd,
        format
      }
    });
    return response.data;
  }

  async getFDAReportingStatus(reportType?: string): Promise<{
    fda_reporting: Record<string, any>;
    report_types: Array<Record<string, any>>;
    compliance_score: number;
    next_deadline: string;
    recommendations: string[];
  }> {
    const response = await apiClient.get(`${this.baseURL}/fda-reporting-status`, {
      params: { report_type: reportType }
    });
    return response.data;
  }

  async runAutomatedComplianceCheck(
    checkType: string,
    scope: string = 'full'
  ): Promise<{ success: boolean; check_id: string; message: string }> {
    const response = await apiClient.post(`${this.baseURL}/automated-compliance-check`, null, {
      params: {
        check_type: checkType,
        scope
      }
    });
    return response.data;
  }

  async getComplianceDashboard(timeframe: string = '30d'): Promise<ComplianceDashboard> {
    const response = await apiClient.get(`${this.baseURL}/compliance-dashboard`, {
      params: { timeframe }
    });
    return response.data;
  }

  async getHealthCheck(): Promise<Record<string, any>> {
    const response = await apiClient.get(`${this.baseURL}/health`);
    return response.data;
  }
}

export const complianceService = new ComplianceService();