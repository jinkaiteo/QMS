// Predictive Scheduling Service - Phase C Frontend Development
import { apiClient } from './apiClient';

export interface PredictionRequest {
  report_type: string;
  department: string;
  target_date: string;
  priority?: 'critical' | 'high' | 'normal' | 'low' | 'batch';
  preferred_time?: string;
  model?: 'historical_pattern' | 'usage_based' | 'department_pattern' | 'seasonal_trend' | 'capacity_optimization' | 'hybrid';
  context?: Record<string, any>;
}

export interface PredictionResponse {
  prediction_id: string;
  recommended_time: string;
  confidence_score: number;
  optimization_factors: string[];
  alternative_times: string[];
  capacity_impact: Record<string, any>;
  risk_assessment: Record<string, number>;
  model_used: string;
  generated_at: string;
}

export interface MLPredictionRequest {
  request_data: Record<string, any>;
  context_data: Record<string, any>;
  model_type?: 'linear_regression' | 'time_series' | 'clustering' | 'ensemble';
}

export interface MLPredictionResponse {
  predicted_value: number;
  confidence_interval: [number, number];
  feature_importance: Record<string, number>;
  model_version: string;
  prediction_timestamp: string;
}

export interface PatternAnalysis {
  analysis_period: Record<string, any>;
  total_deliveries: number;
  success_rate: number;
  peak_hours: number[];
  seasonal_trends: Record<string, number>;
  optimization_opportunities: string[];
  insights: string[];
}

export interface CapacityForecast {
  forecast_period: Record<string, any>;
  total_predicted_deliveries: number;
  average_daily_demand: number;
  peak_demand_days: number;
  bottleneck_risk_days: number;
  daily_forecasts: Array<Record<string, any>>;
  recommendations: string[];
  confidence_metrics: Record<string, number>;
}

export interface OptimizationRequest {
  target_date: string;
  goal?: 'minimize_delays' | 'maximize_capacity' | 'balance_load' | 'reduce_conflicts' | 'optimize_resources';
  constraints?: Record<string, any>;
}

export interface OptimizationResponse {
  recommendation_id: string;
  target_date: string;
  current_schedule: Record<string, any>;
  optimized_schedule: Record<string, any>;
  improvement_metrics: Record<string, number>;
  implementation_effort: string;
  expected_benefits: string[];
  risks: string[];
}

export interface SchedulingInsights {
  analysis_period: string;
  generated_at: string;
  scope: string;
  executive_summary: Record<string, any>;
  key_findings: string[];
  recommendations: string[];
  performance_metrics: Record<string, number>;
  alerts: string[];
}

export interface FeedbackRequest {
  prediction_id: string;
  actual_outcome: Record<string, any>;
  feedback_score: number;
  comments?: string;
}

class PredictiveSchedulingService {
  private baseURL = '/api/v1/predictive-scheduling';

  async predictOptimalTime(request: PredictionRequest): Promise<PredictionResponse> {
    const response = await apiClient.post(`${this.baseURL}/predict`, request);
    return response.data;
  }

  async mlPredict(request: MLPredictionRequest): Promise<MLPredictionResponse> {
    const response = await apiClient.post(`${this.baseURL}/ml-predict`, request);
    return response.data;
  }

  async analyzePatterns(
    daysBack: number = 90,
    department?: string
  ): Promise<PatternAnalysis> {
    const response = await apiClient.get(`${this.baseURL}/analyze-patterns`, {
      params: {
        days_back: daysBack,
        department
      }
    });
    return response.data;
  }

  async forecastCapacity(forecastDays: number = 30): Promise<CapacityForecast> {
    const response = await apiClient.get(`${this.baseURL}/forecast-capacity`, {
      params: { forecast_days: forecastDays }
    });
    return response.data;
  }

  async optimizeSchedule(request: OptimizationRequest): Promise<OptimizationResponse> {
    const response = await apiClient.post(`${this.baseURL}/optimize`, request);
    return response.data;
  }

  async getSchedulingInsights(
    department?: string,
    daysBack: number = 30
  ): Promise<SchedulingInsights> {
    const response = await apiClient.get(`${this.baseURL}/insights`, {
      params: {
        department,
        days_back: daysBack
      }
    });
    return response.data;
  }

  async provideFeedback(feedback: FeedbackRequest): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(`${this.baseURL}/feedback`, feedback);
    return response.data;
  }

  async getModelInsights() {
    const response = await apiClient.get(`${this.baseURL}/model-insights`);
    return response.data;
  }

  async trainModel(
    modelType: string,
    validationSplit: number = 0.2
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(`${this.baseURL}/train-model`, null, {
      params: {
        model_type: modelType,
        validation_split: validationSplit
      }
    });
    return response.data;
  }

  async getHealthCheck() {
    const response = await apiClient.get(`${this.baseURL}/health`);
    return response.data;
  }
}

export const predictiveSchedulingService = new PredictiveSchedulingService();