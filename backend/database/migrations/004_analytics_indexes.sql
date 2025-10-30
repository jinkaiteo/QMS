-- Analytics Performance Indexes - Phase B Sprint 1 Day 1
-- Creates optimized indexes for analytics queries and dashboard performance

-- ========================================
-- ANALYTICS METRICS INDEXES
-- ========================================

-- Primary query indexes for metrics filtering
CREATE INDEX idx_analytics_metrics_category ON analytics_metrics(metric_category);
CREATE INDEX idx_analytics_metrics_subcategory ON analytics_metrics(metric_subcategory);
CREATE INDEX idx_analytics_metrics_name ON analytics_metrics(metric_name);

-- Time-based indexes for date range queries
CREATE INDEX idx_analytics_metrics_measurement_date ON analytics_metrics(measurement_date);
CREATE INDEX idx_analytics_metrics_period_range ON analytics_metrics(period_start, period_end);
CREATE INDEX idx_analytics_metrics_created_at ON analytics_metrics(created_at);

-- Context and scope indexes
CREATE INDEX idx_analytics_metrics_department ON analytics_metrics(department_id);
CREATE INDEX idx_analytics_metrics_user ON analytics_metrics(user_id);
CREATE INDEX idx_analytics_metrics_organization ON analytics_metrics(organization_id);
CREATE INDEX idx_analytics_metrics_module ON analytics_metrics(module_name);

-- Entity relationship indexes
CREATE INDEX idx_analytics_metrics_entity ON analytics_metrics(entity_type, entity_id);

-- Composite indexes for common query patterns
CREATE INDEX idx_analytics_metrics_dept_category_date ON analytics_metrics(department_id, metric_category, measurement_date);
CREATE INDEX idx_analytics_metrics_module_entity_date ON analytics_metrics(module_name, entity_type, measurement_date);
CREATE INDEX idx_analytics_metrics_category_period ON analytics_metrics(metric_category, period_start, period_end);

-- Performance index for active metrics
CREATE INDEX idx_analytics_metrics_active ON analytics_metrics(is_deleted, measurement_date) WHERE is_deleted = FALSE;

-- ========================================
-- REPORT TEMPLATES INDEXES
-- ========================================

-- Primary access indexes
CREATE INDEX idx_report_templates_type ON report_templates(report_type);
CREATE INDEX idx_report_templates_category ON report_templates(category);
CREATE INDEX idx_report_templates_active ON report_templates(is_active) WHERE is_active = TRUE;

-- Creator and ownership indexes
CREATE INDEX idx_report_templates_created_by ON report_templates(created_by);
CREATE INDEX idx_report_templates_visibility ON report_templates(visibility);

-- Usage tracking indexes
CREATE INDEX idx_report_templates_usage_count ON report_templates(usage_count DESC);
CREATE INDEX idx_report_templates_updated_at ON report_templates(updated_at DESC);

-- System vs user templates
CREATE INDEX idx_report_templates_system ON report_templates(is_system_template);

-- Composite index for template discovery
CREATE INDEX idx_report_templates_discovery ON report_templates(is_active, visibility, report_type) WHERE is_deleted = FALSE;

-- ========================================
-- SCHEDULED REPORTS INDEXES
-- ========================================

-- Execution scheduling indexes
CREATE INDEX idx_scheduled_reports_next_run ON scheduled_reports(next_run) WHERE is_active = TRUE AND is_paused = FALSE;
CREATE INDEX idx_scheduled_reports_schedule_type ON scheduled_reports(schedule_type);

-- Template relationship index
CREATE INDEX idx_scheduled_reports_template ON scheduled_reports(template_id);

-- Status tracking indexes
CREATE INDEX idx_scheduled_reports_active ON scheduled_reports(is_active);
CREATE INDEX idx_scheduled_reports_last_run ON scheduled_reports(last_run DESC);
CREATE INDEX idx_scheduled_reports_failures ON scheduled_reports(failure_count, last_failure);

-- Creator access index
CREATE INDEX idx_scheduled_reports_created_by ON scheduled_reports(created_by);

-- ========================================
-- REPORT INSTANCES INDEXES
-- ========================================

-- Template and schedule relationship indexes
CREATE INDEX idx_report_instances_template ON report_instances(template_id);
CREATE INDEX idx_report_instances_scheduled ON report_instances(scheduled_report_id);

-- Generation tracking indexes
CREATE INDEX idx_report_instances_generated_at ON report_instances(generated_at DESC);
CREATE INDEX idx_report_instances_generated_by ON report_instances(generated_by);
CREATE INDEX idx_report_instances_status ON report_instances(status);

-- File management indexes
CREATE INDEX idx_report_instances_format ON report_instances(file_format);
CREATE INDEX idx_report_instances_expires ON report_instances(expires_at);

-- Access tracking indexes
CREATE INDEX idx_report_instances_accessed ON report_instances(last_accessed DESC);
CREATE INDEX idx_report_instances_access_count ON report_instances(access_count DESC);

-- Cleanup index for expired reports
CREATE INDEX idx_report_instances_cleanup ON report_instances(status, expires_at) WHERE status IN ('completed', 'failed');

-- ========================================
-- DASHBOARD CONFIGURATIONS INDEXES
-- ========================================

-- Ownership and access indexes
CREATE INDEX idx_dashboard_configs_owner ON dashboard_configurations(owner_id);
CREATE INDEX idx_dashboard_configs_department ON dashboard_configurations(department_id);
CREATE INDEX idx_dashboard_configs_type ON dashboard_configurations(dashboard_type);

-- Visibility and access control
CREATE INDEX idx_dashboard_configs_visibility ON dashboard_configurations(visibility);
CREATE INDEX idx_dashboard_configs_active ON dashboard_configurations(is_active) WHERE is_active = TRUE;

-- Usage tracking indexes
CREATE INDEX idx_dashboard_configs_usage ON dashboard_configurations(usage_count DESC, last_used DESC);
CREATE INDEX idx_dashboard_configs_default ON dashboard_configurations(is_default) WHERE is_default = TRUE;

-- Creator tracking
CREATE INDEX idx_dashboard_configs_created_by ON dashboard_configurations(created_by);

-- ========================================
-- ANALYTICS CACHE INDEXES
-- ========================================

-- Cache key lookup (already unique)
-- CREATE UNIQUE INDEX idx_analytics_cache_key ON analytics_cache(cache_key); -- Already created by UNIQUE constraint

-- Cache expiration management
CREATE INDEX idx_analytics_cache_expires ON analytics_cache(expires_at);
CREATE INDEX idx_analytics_cache_category ON analytics_cache(cache_category);

-- Context indexes for cache invalidation
CREATE INDEX idx_analytics_cache_department ON analytics_cache(department_id);
CREATE INDEX idx_analytics_cache_user ON analytics_cache(user_id);

-- Performance tracking
CREATE INDEX idx_analytics_cache_hit_count ON analytics_cache(hit_count DESC);
CREATE INDEX idx_analytics_cache_last_hit ON analytics_cache(last_hit DESC);

-- Cache cleanup index
CREATE INDEX idx_analytics_cache_cleanup ON analytics_cache(expires_at, created_at) WHERE expires_at < NOW();

-- ========================================
-- PARTIAL INDEXES FOR PERFORMANCE
-- ========================================

-- Index only active, non-deleted records for better performance
CREATE INDEX idx_analytics_metrics_active_recent ON analytics_metrics(measurement_date DESC, metric_category) 
WHERE is_deleted = FALSE AND measurement_date > (NOW() - INTERVAL '1 year');

-- Index for recent report instances
CREATE INDEX idx_report_instances_recent ON report_instances(generated_at DESC, status) 
WHERE generated_at > (NOW() - INTERVAL '6 months');

-- Index for active scheduled reports ready to run
CREATE INDEX idx_scheduled_reports_ready ON scheduled_reports(next_run ASC) 
WHERE is_active = TRUE AND is_paused = FALSE AND next_run <= NOW();

-- ========================================
-- FUNCTIONAL INDEXES
-- ========================================

-- Index for JSON data queries (if needed for specific use cases)
-- These would be added based on specific query patterns discovered during testing

-- Example: Index for searching report templates by configuration
-- CREATE INDEX idx_report_templates_config_type ON report_templates USING GIN ((config->'type'));

-- Example: Index for dashboard widget types
-- CREATE INDEX idx_dashboard_configs_widgets ON dashboard_configurations USING GIN ((layout->'widgets'));

-- ========================================
-- STATISTICS AND MAINTENANCE
-- ========================================

-- Update statistics for the query planner
ANALYZE analytics_metrics;
ANALYZE report_templates;
ANALYZE scheduled_reports;
ANALYZE report_instances;
ANALYZE dashboard_configurations;
ANALYZE analytics_cache;

-- Add comments for index documentation
COMMENT ON INDEX idx_analytics_metrics_dept_category_date IS 'Composite index for department-level analytics by category and date';
COMMENT ON INDEX idx_report_templates_discovery IS 'Optimized index for template discovery and listing';
COMMENT ON INDEX idx_scheduled_reports_next_run IS 'Critical index for report scheduler execution';
COMMENT ON INDEX idx_analytics_cache_expires IS 'Index for cache expiration cleanup processes';