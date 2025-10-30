-- Report Template Engine Database Migration - Phase B Sprint 2 Day 1
-- Creates comprehensive reporting infrastructure

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- REPORT TEMPLATES TABLE
-- ========================================

CREATE TABLE report_templates (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Template identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL CHECK (category IN ('compliance', 'operational', 'analytical', 'executive')),
    template_type VARCHAR(50) NOT NULL CHECK (template_type IN ('pdf', 'excel', 'dashboard', 'hybrid')),
    
    -- Template configuration
    template_data JSON NOT NULL,
    parameters JSON,
    data_sources JSON,
    layout_config JSON,
    
    -- Metadata
    version INTEGER DEFAULT 1,
    parent_template_id INTEGER REFERENCES report_templates(id),
    tags JSON,
    
    -- Access control
    visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('public', 'private', 'department', 'role')),
    allowed_roles JSON,
    allowed_departments JSON,
    
    -- Status and usage
    is_active BOOLEAN DEFAULT TRUE,
    is_system_template BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    
    -- Performance metadata
    avg_generation_time_ms INTEGER,
    complexity_score INTEGER CHECK (complexity_score >= 1 AND complexity_score <= 10),
    
    -- Audit fields
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ========================================
-- REPORT TEMPLATE PARAMETERS TABLE
-- ========================================

CREATE TABLE report_template_parameters (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES report_templates(id) ON DELETE CASCADE,
    
    -- Parameter definition
    parameter_name VARCHAR(100) NOT NULL,
    parameter_type VARCHAR(50) NOT NULL CHECK (parameter_type IN ('string', 'integer', 'float', 'boolean', 'date', 'datetime', 'array', 'object')),
    
    -- Validation rules
    is_required BOOLEAN DEFAULT FALSE,
    default_value JSON,
    validation_rules JSON,
    
    -- UI configuration
    display_name VARCHAR(255),
    description TEXT,
    input_type VARCHAR(50),
    input_options JSON,
    
    -- Position and grouping
    display_order INTEGER DEFAULT 0,
    parameter_group VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- REPORT GENERATION QUEUE TABLE
-- ========================================

CREATE TABLE report_generation_queue (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Job identification
    template_id INTEGER REFERENCES report_templates(id) NOT NULL,
    scheduled_report_id INTEGER REFERENCES scheduled_reports(id),
    
    -- Generation parameters
    parameters JSON NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    
    -- Execution details
    worker_id VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Result information
    output_file_path VARCHAR(500),
    output_file_size INTEGER,
    generation_time_ms INTEGER,
    
    -- Audit fields
    requested_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- REPORT INSTANCES TABLE (Enhanced)
-- ========================================

CREATE TABLE report_instances (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Instance identification
    template_id INTEGER REFERENCES report_templates(id) NOT NULL,
    scheduled_report_id INTEGER REFERENCES scheduled_reports(id),
    queue_job_id INTEGER REFERENCES report_generation_queue(id),
    
    -- Generation details
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by INTEGER REFERENCES users(id),
    generation_time_ms INTEGER,
    
    -- File information
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    file_format VARCHAR(10) NOT NULL CHECK (file_format IN ('pdf', 'xlsx', 'csv', 'json')),
    file_hash VARCHAR(64),
    mime_type VARCHAR(100),
    
    -- Report metadata
    title VARCHAR(255),
    description TEXT,
    parameters JSON,
    data_range JSON,
    record_count INTEGER,
    page_count INTEGER,
    
    -- Access control and sharing
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    last_accessed_by INTEGER REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_public BOOLEAN DEFAULT FALSE,
    shared_with JSON,
    
    -- Status and lifecycle
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'expired', 'deleted')),
    archived_at TIMESTAMP WITH TIME ZONE,
    
    -- Performance metrics
    download_count INTEGER DEFAULT 0,
    email_count INTEGER DEFAULT 0,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================

-- Report Templates indexes
CREATE INDEX idx_report_templates_category ON report_templates(category);
CREATE INDEX idx_report_templates_type ON report_templates(template_type);
CREATE INDEX idx_report_templates_active ON report_templates(is_active, is_deleted);
CREATE INDEX idx_report_templates_usage ON report_templates(usage_count DESC);
CREATE INDEX idx_report_templates_created_by ON report_templates(created_by);

-- Report Template Parameters indexes
CREATE INDEX idx_template_parameters_template ON report_template_parameters(template_id);
CREATE INDEX idx_template_parameters_order ON report_template_parameters(template_id, display_order);

-- Report Generation Queue indexes
CREATE INDEX idx_report_queue_status ON report_generation_queue(status);
CREATE INDEX idx_report_queue_priority ON report_generation_queue(priority, created_at);
CREATE INDEX idx_report_queue_template ON report_generation_queue(template_id);
CREATE INDEX idx_report_queue_worker ON report_generation_queue(worker_id, status);

-- Report Instances indexes
CREATE INDEX idx_report_instances_template ON report_instances(template_id);
CREATE INDEX idx_report_instances_generated ON report_instances(generated_at DESC);
CREATE INDEX idx_report_instances_user ON report_instances(generated_by);
CREATE INDEX idx_report_instances_expires ON report_instances(expires_at);
CREATE INDEX idx_report_instances_status ON report_instances(status);
CREATE INDEX idx_report_instances_access ON report_instances(access_count DESC);

-- ========================================
-- CONSTRAINTS AND UNIQUE INDEXES
-- ========================================

-- Unique template names per user
CREATE UNIQUE INDEX uk_report_templates_name_user ON report_templates(name, created_by) WHERE is_deleted = FALSE;

-- Unique parameter names per template
CREATE UNIQUE INDEX uk_template_parameter_name ON report_template_parameters(template_id, parameter_name);

-- ========================================
-- SAMPLE REPORT TEMPLATES
-- ========================================

-- Executive Quality Summary Template
INSERT INTO report_templates (name, description, category, template_type, template_data, parameters, data_sources, is_system_template, created_by, complexity_score) VALUES
('Executive Quality Summary', 'High-level quality overview for executives', 'executive', 'pdf', 
'{"title": "Executive Quality Summary", "sections": [{"type": "kpi_grid", "title": "Key Performance Indicators", "data_key": "kpis"}, {"type": "chart", "title": "Quality Trends", "chart_type": "line", "data_key": "trends"}, {"type": "table", "title": "Department Performance", "data_key": "departments"}], "show_metadata": true}',
'{"period_days": {"type": "integer", "default": 30, "description": "Analysis period in days"}, "departments": {"type": "array", "optional": true, "description": "Specific departments to include"}}',
'[{"name": "quality_metrics", "endpoint": "/api/v1/analytics/dashboards/quality"}, {"name": "department_data", "endpoint": "/api/v1/analytics/departments/analytics"}]',
true, 1, 7);

-- Training Compliance Report Template
INSERT INTO report_templates (name, description, category, template_type, template_data, parameters, data_sources, is_system_template, created_by, complexity_score) VALUES
('Training Compliance Report', 'Detailed training compliance status and analysis', 'compliance', 'excel',
'{"title": "Training Compliance Report", "sheets": [{"name": "Summary", "type": "summary"}, {"name": "By Department", "type": "department_breakdown"}, {"name": "Individual Status", "type": "user_details"}, {"name": "Overdue Training", "type": "overdue_analysis"}]}',
'{"department_id": {"type": "integer", "optional": true, "description": "Specific department filter"}, "include_completed": {"type": "boolean", "default": true, "description": "Include completed training"}}',
'[{"name": "training_metrics", "endpoint": "/api/v1/analytics/dashboards/training"}, {"name": "user_training", "endpoint": "/api/v1/training/assignments"}]',
true, 1, 6);

-- Quality Event Analysis Template
INSERT INTO report_templates (name, description, category, template_type, template_data, parameters, data_sources, is_system_template, created_by, complexity_score) VALUES
('Quality Event Analysis', 'Comprehensive quality event analysis and trends', 'analytical', 'pdf',
'{"title": "Quality Event Analysis Report", "sections": [{"type": "text", "title": "Executive Summary", "data_key": "summary"}, {"type": "chart", "title": "Event Trends", "chart_type": "line", "data_key": "event_trends"}, {"type": "chart", "title": "Events by Severity", "chart_type": "pie", "data_key": "severity_breakdown"}, {"type": "table", "title": "Top Issues", "data_key": "top_issues"}]}',
'{"start_date": {"type": "date", "required": true, "description": "Analysis start date"}, "end_date": {"type": "date", "required": true, "description": "Analysis end date"}, "severity_filter": {"type": "array", "optional": true, "description": "Filter by severity levels"}}',
'[{"name": "quality_events", "endpoint": "/api/v1/quality-events"}, {"name": "quality_metrics", "endpoint": "/api/v1/analytics/metrics/quality"}]',
true, 1, 8);

-- ========================================
-- SAMPLE TEMPLATE PARAMETERS
-- ========================================

-- Parameters for Executive Quality Summary
INSERT INTO report_template_parameters (template_id, parameter_name, parameter_type, is_required, default_value, display_name, description, input_type, display_order) VALUES
(1, 'period_days', 'integer', false, '30', 'Analysis Period (days)', 'Number of days to include in the analysis', 'number', 1),
(1, 'departments', 'array', false, null, 'Departments', 'Specific departments to include (leave empty for all)', 'multi-select', 2);

-- Parameters for Training Compliance Report
INSERT INTO report_template_parameters (template_id, parameter_name, parameter_type, is_required, default_value, display_name, description, input_type, display_order) VALUES
(2, 'department_id', 'integer', false, null, 'Department', 'Filter by specific department', 'select', 1),
(2, 'include_completed', 'boolean', false, 'true', 'Include Completed Training', 'Include completed training in the report', 'checkbox', 2);

-- Parameters for Quality Event Analysis
INSERT INTO report_template_parameters (template_id, parameter_name, parameter_type, is_required, default_value, display_name, description, input_type, display_order) VALUES
(3, 'start_date', 'date', true, null, 'Start Date', 'Analysis period start date', 'date', 1),
(3, 'end_date', 'date', true, null, 'End Date', 'Analysis period end date', 'date', 2),
(3, 'severity_filter', 'array', false, null, 'Severity Levels', 'Filter by specific severity levels', 'multi-select', 3);

-- ========================================
-- COMMENTS AND DOCUMENTATION
-- ========================================

COMMENT ON TABLE report_templates IS 'Defines reusable report templates with configuration and parameters';
COMMENT ON TABLE report_template_parameters IS 'Parameters for report templates with validation and UI configuration';
COMMENT ON TABLE report_generation_queue IS 'Background job queue for report generation processing';
COMMENT ON TABLE report_instances IS 'Generated report instances with file information and access tracking';

-- Add column comments for key fields
COMMENT ON COLUMN report_templates.template_data IS 'Complete JSON template definition including sections, layout, and formatting';
COMMENT ON COLUMN report_templates.complexity_score IS 'Template complexity score (1-10) for resource planning and optimization';
COMMENT ON COLUMN report_generation_queue.priority IS 'Job priority (1=highest, 10=lowest) for queue processing order';
COMMENT ON COLUMN report_instances.file_hash IS 'SHA-256 hash of generated file for integrity verification';