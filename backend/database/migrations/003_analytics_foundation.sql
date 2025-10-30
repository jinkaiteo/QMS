-- Analytics Foundation Migration - Phase B Sprint 1 Day 1
-- Creates core analytics tables for the QMS reporting system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- ANALYTICS METRICS TABLE
-- ========================================

CREATE TABLE analytics_metrics (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Metric identification
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL CHECK (metric_category IN ('quality', 'training', 'documents', 'organizational', 'compliance')),
    metric_subcategory VARCHAR(50),
    
    -- Metric values
    value DECIMAL(15,4),
    value_text VARCHAR(500),
    unit VARCHAR(20) CHECK (unit IN ('percentage', 'count', 'days', 'hours', 'score', 'currency', 'ratio')),
    
    -- Context and scope
    department_id INTEGER REFERENCES departments(id),
    user_id INTEGER REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    module_name VARCHAR(50) CHECK (module_name IN ('edms', 'lims', 'tms', 'qrm', 'organization')),
    entity_type VARCHAR(50),
    entity_id INTEGER,
    
    -- Time dimensions
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    measurement_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    calculation_method VARCHAR(100),
    data_source VARCHAR(100),
    confidence_level DECIMAL(5,2) CHECK (confidence_level >= 0 AND confidence_level <= 100),
    tags JSON,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ========================================
-- REPORT TEMPLATES TABLE
-- ========================================

CREATE TABLE report_templates (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Template identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) NOT NULL CHECK (report_type IN ('dashboard', 'compliance', 'operational', 'custom', 'executive')),
    category VARCHAR(50) CHECK (category IN ('quality', 'training', 'documents', 'organization', 'cross_module')),
    
    -- Template configuration
    config JSON NOT NULL,
    data_sources JSON,
    parameters JSON,
    layout JSON,
    
    -- Access control
    visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('public', 'private', 'department', 'role')),
    allowed_roles JSON,
    allowed_departments JSON,
    
    -- Template metadata
    version INTEGER DEFAULT 1,
    parent_template_id INTEGER REFERENCES report_templates(id),
    is_active BOOLEAN DEFAULT TRUE,
    is_system_template BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    
    -- Audit fields
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    CONSTRAINT uk_report_templates_name_user UNIQUE(name, created_by)
);

-- ========================================
-- SCHEDULED REPORTS TABLE
-- ========================================

CREATE TABLE scheduled_reports (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Schedule identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_id INTEGER REFERENCES report_templates(id) NOT NULL,
    
    -- Scheduling configuration
    schedule_type VARCHAR(20) NOT NULL CHECK (schedule_type IN ('cron', 'interval', 'manual')),
    schedule_cron VARCHAR(50),
    schedule_interval INTEGER CHECK (schedule_interval > 0),
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Execution times
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    last_success TIMESTAMP WITH TIME ZONE,
    last_failure TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    
    -- Delivery configuration
    delivery_method VARCHAR(20) DEFAULT 'email' CHECK (delivery_method IN ('email', 'download', 'api', 'storage')),
    recipients JSON,
    delivery_options JSON,
    
    -- Report parameters
    parameters JSON,
    output_format VARCHAR(10) DEFAULT 'pdf' CHECK (output_format IN ('pdf', 'excel', 'csv', 'json')),
    
    -- Status and control
    is_active BOOLEAN DEFAULT TRUE,
    is_paused BOOLEAN DEFAULT FALSE,
    max_failures INTEGER DEFAULT 3,
    
    -- Audit fields
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ========================================
-- REPORT INSTANCES TABLE
-- ========================================

CREATE TABLE report_instances (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Instance identification
    template_id INTEGER REFERENCES report_templates(id) NOT NULL,
    scheduled_report_id INTEGER REFERENCES scheduled_reports(id),
    
    -- Generation details
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by INTEGER REFERENCES users(id),
    generation_time_ms INTEGER,
    
    -- File information
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_size_bytes BIGINT,
    file_format VARCHAR(10) NOT NULL CHECK (file_format IN ('pdf', 'excel', 'csv', 'json')),
    file_hash VARCHAR(64),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'completed', 'failed', 'expired')),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Report metadata
    parameters JSON,
    data_range JSON,
    record_count INTEGER,
    
    -- Access control
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ========================================
-- DASHBOARD CONFIGURATIONS TABLE
-- ========================================

CREATE TABLE dashboard_configurations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Dashboard identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dashboard_type VARCHAR(50) NOT NULL CHECK (dashboard_type IN ('personal', 'department', 'executive', 'system')),
    
    -- Configuration
    layout JSON NOT NULL,
    refresh_interval INTEGER DEFAULT 300 CHECK (refresh_interval > 0),
    auto_refresh BOOLEAN DEFAULT TRUE,
    
    -- Access control
    owner_id INTEGER REFERENCES users(id),
    department_id INTEGER REFERENCES departments(id),
    visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('public', 'private', 'department')),
    allowed_users JSON,
    allowed_roles JSON,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ========================================
-- ANALYTICS CACHE TABLE
-- ========================================

CREATE TABLE analytics_cache (
    id SERIAL PRIMARY KEY,
    
    -- Cache identification
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    cache_category VARCHAR(50) CHECK (cache_category IN ('dashboard', 'report', 'metric')),
    
    -- Cached data
    data JSON NOT NULL,
    data_hash VARCHAR(64),
    
    -- Cache metadata
    department_id INTEGER REFERENCES departments(id),
    user_id INTEGER REFERENCES users(id),
    parameters JSON,
    
    -- Cache control
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_hit TIMESTAMP WITH TIME ZONE
);

-- ========================================
-- COMMENTS AND DOCUMENTATION
-- ========================================

COMMENT ON TABLE analytics_metrics IS 'Stores all metrics collected across the QMS platform for analytics and reporting';
COMMENT ON TABLE report_templates IS 'Defines reusable report templates with configuration and access control';
COMMENT ON TABLE scheduled_reports IS 'Manages automated report generation and delivery schedules';
COMMENT ON TABLE report_instances IS 'Tracks individual report generation instances and file storage';
COMMENT ON TABLE dashboard_configurations IS 'Stores user and system dashboard configurations and layouts';
COMMENT ON TABLE analytics_cache IS 'Caches computed analytics results for improved performance';

-- Add column comments for key fields
COMMENT ON COLUMN analytics_metrics.metric_category IS 'Primary category: quality, training, documents, organizational, compliance';
COMMENT ON COLUMN analytics_metrics.confidence_level IS 'Confidence level in the metric accuracy (0-100%)';
COMMENT ON COLUMN report_templates.config IS 'Complete JSON configuration defining report structure and data sources';
COMMENT ON COLUMN scheduled_reports.schedule_cron IS 'Cron expression for complex scheduling patterns';
COMMENT ON COLUMN analytics_cache.cache_key IS 'Unique identifier for cached data, includes context and parameters';