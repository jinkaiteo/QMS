// Advanced Analytics Service - Phase C Frontend Development
import { apiClient } from './apiClient';

export interface DashboardMetrics {
  total_users: number;
  active_documents: number;
  pending_trainings: number;
  open_quality_events: number;
  system_utilization: number;
  compliance_score: number;
  generated_at: string;
}

export interface ModuleHealth {
  module_name: string;
  status: string;
  last_activity: string;
  active_users: number;
  error_rate: number;
  performance_score: number;
}

export interface AnalyticsInsight {
  insight_id: string;
  category: string;
  title: string;
  description: string;
  impact_level: string;
  action_required: boolean;
  data_points: Record<string, any>;
  generated_at: string;
}

export interface TrendAnalysis {
  metric_name: string;
  time_period: string;
  data_points: Array<{ date: string; value: number }>;
  trend_direction: string;
  percentage_change: number;
  confidence_level: number;
}

export interface ComplianceStatus {
  overall_score: number;
  module_scores: Record<string, number>;
  critical_issues: string[];
  recommendations: string[];
  audit_readiness: string;
  last_assessment: string;
}

export interface SystemPerformance {
  cpu_usage: number;
  memory_usage: number;
  database_connections: number;
  api_response_time: number;
  error_rate: number;
  uptime_percentage: number;
}

export interface PredictiveInsights {
  capacity_forecast: Record<string, any>;
  bottleneck_predictions: string[];
  optimization_opportunities: string[];
  risk_assessments: Record<string, number>;
  confidence_scores: Record<string, number>;
}

class AdvancedAnalyticsService {
  private baseURL = '/api/v1/advanced-analytics';

  async getDashboardOverview(dateRange: number = 30): Promise<DashboardMetrics> {
    const response = await apiClient.get(`${this.baseURL}/dashboard-overview`, {
      params: { date_range: dateRange }
    });
    return response.data;
  }

  async getModuleHealth(): Promise<ModuleHealth[]> {
    const response = await apiClient.get(`${this.baseURL}/module-health`);
    return response.data;
  }

  async getAnalyticsInsights(
    category?: string,
    priority?: string,
    limit: number = 10
  ): Promise<AnalyticsInsight[]> {
    const response = await apiClient.get(`${this.baseURL}/analytics-insights`, {
      params: {
        category,
        priority,
        limit
      }
    });
    return response.data;
  }

  async getTrendAnalysis(
    metrics: string[],
    timePeriod: string = '30d'
  ): Promise<TrendAnalysis[]> {
    const response = await apiClient.get(`${this.baseURL}/trend-analysis`, {
      params: {
        metrics,
        time_period: timePeriod
      }
    });
    return response.data;
  }

  async getComplianceStatus(): Promise<ComplianceStatus> {
    const response = await apiClient.get(`${this.baseURL}/compliance-status`);
    return response.data;
  }

  async getSystemPerformance(): Promise<SystemPerformance> {
    const response = await apiClient.get(`${this.baseURL}/system-performance`);
    return response.data;
  }

  async getPredictiveInsights(forecastDays: number = 30): Promise<PredictiveInsights> {
    const response = await apiClient.get(`${this.baseURL}/predictive-insights`, {
      params: { forecast_days: forecastDays }
    });
    return response.data;
  }

  async getDepartmentAnalytics(departmentId: number, timePeriod: string = '30d') {
    const response = await apiClient.get(`${this.baseURL}/department-analytics/${departmentId}`, {
      params: { time_period: timePeriod }
    });
    return response.data;
  }

  async generateReport(
    reportType: string,
    modules: string[],
    format: string = 'pdf'
  ) {
    const response = await apiClient.post(`${this.baseURL}/generate-report`, null, {
      params: {
        report_type: reportType,
        modules,
        format
      }
    });
    return response.data;
  }

  async exportData(
    dataType: string,
    startDate: string,
    endDate: string,
    format: string = 'json'
  ) {
    const response = await apiClient.get(`${this.baseURL}/export-data`, {
      params: {
        data_type: dataType,
        start_date: startDate,
        end_date: endDate,
        format
      }
    });
    return response.data;
  }

  async getHealthCheck() {
    const response = await apiClient.get(`${this.baseURL}/health`);
    return response.data;
  }
}

export const advancedAnalyticsService = new AdvancedAnalyticsService();