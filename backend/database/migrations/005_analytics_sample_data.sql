-- Analytics Sample Data - Phase B Sprint 1 Day 1
-- Inserts sample data for testing and development of analytics features

-- ========================================
-- SAMPLE ANALYTICS METRICS
-- ========================================

-- Quality Metrics
INSERT INTO analytics_metrics (metric_name, metric_category, metric_subcategory, value, unit, department_id, module_name, entity_type, period_start, period_end, measurement_date, calculation_method, data_source, confidence_level, created_by) VALUES
('Quality Events Count', 'quality', 'events', 15, 'count', 1, 'qrm', 'quality_event', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'direct_count', 'quality_events_table', 100.0, 1),
('Average Resolution Time', 'quality', 'performance', 5.5, 'days', 1, 'qrm', 'quality_event', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'average_calculation', 'quality_events_table', 95.0, 1),
('CAPA Effectiveness Rate', 'quality', 'effectiveness', 87.5, 'percentage', 1, 'qrm', 'capa', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'effectiveness_ratio', 'capas_table', 90.0, 1),
('Compliance Score', 'compliance', 'overall', 94.2, 'score', 1, 'qrm', 'department', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'weighted_average', 'multiple_sources', 85.0, 1),

-- Training Metrics
('Training Completion Rate', 'training', 'completion', 92.3, 'percentage', 1, 'tms', 'training_assignment', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'completion_ratio', 'training_assignments_table', 100.0, 1),
('Overdue Training Count', 'training', 'compliance', 8, 'count', 1, 'tms', 'training_assignment', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'direct_count', 'training_assignments_table', 100.0, 1),
('Average Training Score', 'training', 'performance', 88.7, 'score', 1, 'tms', 'training_assignment', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'average_calculation', 'training_assignments_table', 95.0, 1),
('Training Hours Completed', 'training', 'volume', 245, 'hours', 1, 'tms', 'training_assignment', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'sum_calculation', 'training_assignments_table', 100.0, 1),

-- Document Metrics
('Documents Created', 'documents', 'creation', 23, 'count', 1, 'edms', 'document', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'direct_count', 'documents_table', 100.0, 1),
('Average Approval Time', 'documents', 'workflow', 3.2, 'days', 1, 'edms', 'document', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'average_calculation', 'documents_table', 90.0, 1),
('Document Access Count', 'documents', 'usage', 1456, 'count', 1, 'edms', 'document', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'access_log_count', 'audit_logs_table', 85.0, 1),
('Revision Rate', 'documents', 'quality', 12.5, 'percentage', 1, 'edms', 'document', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'revision_ratio', 'documents_table', 88.0, 1),

-- Organizational Metrics
('Active Users', 'organizational', 'engagement', 47, 'count', NULL, 'organization', 'user', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'active_user_count', 'user_sessions_table', 100.0, 1),
('Department Efficiency Score', 'organizational', 'performance', 91.3, 'score', 1, 'organization', 'department', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'weighted_score', 'multiple_sources', 80.0, 1),
('Cross-Department Collaboration', 'organizational', 'collaboration', 76.4, 'score', NULL, 'organization', 'department', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'collaboration_index', 'audit_logs_table', 75.0, 1),

-- Additional metrics for different departments
('Quality Events Count', 'quality', 'events', 12, 'count', 2, 'qrm', 'quality_event', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'direct_count', 'quality_events_table', 100.0, 1),
('Training Completion Rate', 'training', 'completion', 89.1, 'percentage', 2, 'tms', 'training_assignment', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'completion_ratio', 'training_assignments_table', 100.0, 1),
('Quality Events Count', 'quality', 'events', 8, 'count', 3, 'qrm', 'quality_event', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'direct_count', 'quality_events_table', 100.0, 1),
('Training Completion Rate', 'training', 'completion', 95.7, 'percentage', 3, 'tms', 'training_assignment', '2024-01-01 00:00:00+00', '2024-01-31 23:59:59+00', '2024-02-01 09:00:00+00', 'completion_ratio', 'training_assignments_table', 100.0, 1);

-- ========================================
-- SAMPLE REPORT TEMPLATES
-- ========================================

-- Executive Dashboard Template
INSERT INTO report_templates (name, description, report_type, category, config, data_sources, parameters, layout, visibility, is_system_template, created_by) VALUES
('Executive Quality Dashboard', 'High-level quality metrics overview for executives', 'dashboard', 'quality', 
'{"title": "Executive Quality Dashboard", "type": "dashboard", "widgets": ["quality_kpis", "compliance_gauge", "trend_chart", "department_comparison"]}',
'[{"name": "quality_metrics", "table": "analytics_metrics", "filters": {"metric_category": "quality"}}, {"name": "compliance_data", "table": "analytics_metrics", "filters": {"metric_category": "compliance"}}]',
'{"period_days": {"type": "integer", "default": 30, "description": "Number of days for analysis"}, "departments": {"type": "array", "optional": true, "description": "Specific departments to include"}}',
'{"grid": {"columns": 12, "rows": 8}, "widgets": [{"id": "quality_kpis", "x": 0, "y": 0, "w": 6, "h": 2}, {"id": "compliance_gauge", "x": 6, "y": 0, "w": 6, "h": 2}]}',
'public', true, 1);

-- Training Compliance Report Template  
INSERT INTO report_templates (name, description, report_type, category, config, data_sources, parameters, layout, visibility, is_system_template, created_by) VALUES
('Training Compliance Report', 'Detailed training completion and compliance status', 'compliance', 'training',
'{"title": "Training Compliance Report", "type": "tabular", "sections": ["summary", "department_breakdown", "individual_status", "overdue_training"]}',
'[{"name": "training_metrics", "table": "analytics_metrics", "filters": {"metric_category": "training"}}, {"name": "training_assignments", "table": "training_assignments"}]',
'{"department_id": {"type": "integer", "optional": true, "description": "Specific department filter"}, "include_completed": {"type": "boolean", "default": true}}',
'{"format": "tabular", "sections": [{"name": "summary", "type": "metrics"}, {"name": "breakdown", "type": "table"}]}',
'department', true, 1);

-- Quality Trend Analysis Template
INSERT INTO report_templates (name, description, report_type, category, config, data_sources, parameters, layout, visibility, is_system_template, created_by) VALUES
('Quality Trend Analysis', 'Historical quality metrics and trend analysis', 'operational', 'quality',
'{"title": "Quality Trend Analysis", "type": "analytical", "charts": ["trend_line", "correlation_matrix", "forecast"]}',
'[{"name": "historical_quality", "table": "analytics_metrics", "filters": {"metric_category": "quality"}, "time_range": "6_months"}]',
'{"period_months": {"type": "integer", "default": 6, "min": 1, "max": 24}, "metrics": {"type": "array", "default": ["Quality Events Count", "CAPA Effectiveness Rate"]}}',
'{"chart_type": "time_series", "secondary_axis": true, "forecast_periods": 3}',
'public', true, 1);

-- Custom Department Performance Template
INSERT INTO report_templates (name, description, report_type, category, config, data_sources, parameters, layout, visibility, created_by) VALUES
('Department Performance Overview', 'Comprehensive department performance metrics', 'custom', 'organizational',
'{"title": "Department Performance", "type": "mixed", "sections": ["kpis", "comparisons", "trends"]}',
'[{"name": "dept_metrics", "table": "analytics_metrics", "join": "departments"}, {"name": "user_activity", "table": "user_sessions"}]',
'{"departments": {"type": "array", "required": true}, "comparison_period": {"type": "string", "default": "previous_month"}}',
'{"layout": "grid", "responsive": true}',
'private', 1);

-- ========================================
-- SAMPLE SCHEDULED REPORTS
-- ========================================

-- Weekly Executive Summary
INSERT INTO scheduled_reports (name, description, template_id, schedule_type, schedule_cron, timezone, delivery_method, recipients, parameters, output_format, created_by) VALUES
('Weekly Executive Summary', 'Automated weekly quality summary for executives', 1, 'cron', '0 8 * * 1', 'UTC', 'email', 
'["executive@company.com", "quality.director@company.com"]',
'{"period_days": 7}', 'pdf', 1);

-- Monthly Training Compliance Report
INSERT INTO scheduled_reports (name, description, template_id, schedule_type, schedule_cron, timezone, delivery_method, recipients, parameters, output_format, created_by) VALUES
('Monthly Training Compliance', 'Monthly training compliance report for HR and Quality', 2, 'cron', '0 9 1 * *', 'UTC', 'email',
'["hr@company.com", "training.manager@company.com"]',
'{"include_completed": true}', 'excel', 1);

-- Daily Quality Metrics
INSERT INTO scheduled_reports (name, description, template_id, schedule_type, schedule_interval, delivery_method, recipients, parameters, output_format, created_by) VALUES
('Daily Quality Metrics', 'Daily quality metrics dashboard data', 1, 'interval', 1440, 'api',
'[]',
'{"period_days": 1}', 'json', 1);

-- ========================================
-- SAMPLE DASHBOARD CONFIGURATIONS
-- ========================================

-- Executive Dashboard Configuration
INSERT INTO dashboard_configurations (name, description, dashboard_type, layout, refresh_interval, owner_id, visibility, is_default, created_by) VALUES
('Executive Overview', 'Executive-level quality and compliance overview', 'executive',
'{"widgets": [
  {"id": "quality_summary", "type": "kpi_card", "x": 0, "y": 0, "w": 3, "h": 2, "config": {"metric": "Quality Events Count", "trend": true}},
  {"id": "compliance_gauge", "type": "gauge", "x": 3, "y": 0, "w": 3, "h": 2, "config": {"metric": "Compliance Score", "thresholds": [70, 85, 95]}},
  {"id": "training_status", "type": "progress", "x": 6, "y": 0, "w": 3, "h": 2, "config": {"metric": "Training Completion Rate"}},
  {"id": "department_comparison", "type": "bar_chart", "x": 9, "y": 0, "w": 3, "h": 2, "config": {"metrics": ["Quality Events Count"], "group_by": "department"}},
  {"id": "quality_trends", "type": "line_chart", "x": 0, "y": 2, "w": 6, "h": 3, "config": {"metrics": ["Quality Events Count", "CAPA Effectiveness Rate"], "period": "30_days"}},
  {"id": "alerts_panel", "type": "alert_list", "x": 6, "y": 2, "w": 6, "h": 3, "config": {"categories": ["quality", "training", "compliance"]}}
]}', 300, 1, 'public', true, 1);

-- Quality Manager Dashboard
INSERT INTO dashboard_configurations (name, description, dashboard_type, layout, refresh_interval, owner_id, department_id, visibility, created_by) VALUES
('Quality Management Dashboard', 'Detailed quality metrics for quality managers', 'department',
'{"widgets": [
  {"id": "capa_effectiveness", "type": "gauge", "x": 0, "y": 0, "w": 4, "h": 2, "config": {"metric": "CAPA Effectiveness Rate"}},
  {"id": "resolution_time", "type": "kpi_card", "x": 4, "y": 0, "w": 4, "h": 2, "config": {"metric": "Average Resolution Time", "target": 5}},
  {"id": "event_trends", "type": "line_chart", "x": 8, "y": 0, "w": 4, "h": 2, "config": {"metric": "Quality Events Count", "period": "90_days"}},
  {"id": "event_breakdown", "type": "pie_chart", "x": 0, "y": 2, "w": 6, "h": 3, "config": {"breakdown_by": "event_type"}},
  {"id": "department_performance", "type": "table", "x": 6, "y": 2, "w": 6, "h": 3, "config": {"metrics": ["Quality Events Count", "CAPA Effectiveness Rate"], "group_by": "department"}}
]}', 180, 2, 1, 'department', 2);

-- Personal Analytics Dashboard
INSERT INTO dashboard_configurations (name, description, dashboard_type, layout, refresh_interval, owner_id, visibility, created_by) VALUES
('My Performance Dashboard', 'Personal performance and activity dashboard', 'personal',
'{"widgets": [
  {"id": "my_training", "type": "progress_ring", "x": 0, "y": 0, "w": 3, "h": 2, "config": {"metric": "Training Completion Rate", "personal": true}},
  {"id": "my_documents", "type": "kpi_card", "x": 3, "y": 0, "w": 3, "h": 2, "config": {"metric": "Documents Created", "personal": true}},
  {"id": "my_activity", "type": "calendar_heatmap", "x": 6, "y": 0, "w": 6, "h": 2, "config": {"metric": "Login Activity", "period": "30_days"}},
  {"id": "assigned_tasks", "type": "task_list", "x": 0, "y": 2, "w": 12, "h": 3, "config": {"source": "quality_events", "filter": "assigned_to_me"}}
]}', 900, 3, 'private', 3);

-- ========================================
-- SAMPLE ANALYTICS CACHE ENTRIES
-- ========================================

-- Cache some computed dashboard data
INSERT INTO analytics_cache (cache_key, cache_category, data, department_id, parameters, expires_at) VALUES
('dashboard_quality_summary_dept_1_30d', 'dashboard', 
'{"quality_events": 15, "avg_resolution": 5.5, "capa_effectiveness": 87.5, "compliance_score": 94.2, "trend": "improving"}',
1, '{"period_days": 30, "department_id": 1}', NOW() + INTERVAL '1 hour');

INSERT INTO analytics_cache (cache_key, cache_category, data, parameters, expires_at) VALUES
('report_executive_overview_global', 'report',
'{"total_quality_events": 35, "avg_training_completion": 92.3, "overall_compliance": 91.8, "active_capas": 12, "departments": 3}',
'{"scope": "global", "period": "current_month"}', NOW() + INTERVAL '4 hours');

INSERT INTO analytics_cache (cache_key, cache_category, data, department_id, user_id, parameters, expires_at) VALUES
('metrics_training_personal_user_3', 'metric',
'{"completion_rate": 95.0, "hours_completed": 24, "certifications": 3, "overdue_count": 0}',
NULL, 3, '{"metric_type": "training", "user_id": 3}', NOW() + INTERVAL '2 hours');

-- ========================================
-- UPDATE SEQUENCES AND FINAL SETUP
-- ========================================

-- Update created_at timestamps to have some historical data
UPDATE analytics_metrics SET created_at = created_at - INTERVAL '30 days' WHERE id <= 5;
UPDATE analytics_metrics SET created_at = created_at - INTERVAL '15 days' WHERE id BETWEEN 6 AND 10;
UPDATE analytics_metrics SET created_at = created_at - INTERVAL '7 days' WHERE id BETWEEN 11 AND 15;

-- Set next run times for scheduled reports
UPDATE scheduled_reports SET next_run = NOW() + INTERVAL '1 week' WHERE id = 1;
UPDATE scheduled_reports SET next_run = DATE_TRUNC('month', NOW()) + INTERVAL '1 month' + INTERVAL '9 hours' WHERE id = 2;
UPDATE scheduled_reports SET next_run = NOW() + INTERVAL '1 day' WHERE id = 3;

-- Update statistics for optimal query planning
ANALYZE analytics_metrics;
ANALYZE report_templates;
ANALYZE scheduled_reports;
ANALYZE report_instances;
ANALYZE dashboard_configurations;
ANALYZE analytics_cache;