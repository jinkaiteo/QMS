# 🚀 Phase B Sprint 1 Day 1 - Analytics Database Design

**Phase**: B - Advanced Reporting & Analytics  
**Sprint**: 1 - Analytics Foundation & Data Model  
**Day**: 1 - Analytics Database Design  
**Focus**: Creating the foundational data model for metrics, reports, and analytics

---

## 🎯 **Day 1 Objectives**

### **Primary Goals:**
- [ ] Design comprehensive analytics database schema
- [ ] Create metrics collection tables
- [ ] Design report templates and scheduling system
- [ ] Implement database migrations for analytics tables
- [ ] Test analytics schema with sample data

### **Deliverables:**
- Analytics database migration files
- Sample analytics data for testing
- Documentation of analytics data model
- Database relationship diagram

---

## 🗄️ **Analytics Database Schema Design**

### **Core Analytics Tables:**

#### **1. Analytics Metrics Table**
```sql
-- Stores all metrics collected across the QMS platform
CREATE TABLE analytics_metrics (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Metric identification
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL, -- 'quality', 'training', 'documents', 'organizational', 'compliance'
    metric_subcategory VARCHAR(50), -- More specific categorization
    
    -- Metric values
    value DECIMAL(15,4), -- Numeric value
    value_text VARCHAR(500), -- Text value for non-numeric metrics
    unit VARCHAR(20), -- 'percentage', 'count', 'days', 'hours', 'score', 'currency'
    
    -- Context and scope
    department_id INTEGER REFERENCES departments(id),
    user_id INTEGER REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    module_name VARCHAR(50), -- 'edms', 'lims', 'tms', 'qrm', 'organization'
    entity_type VARCHAR(50), -- 'document', 'training', 'quality_event', 'user', etc.
    entity_id INTEGER, -- ID of the related entity
    
    -- Time dimensions
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    measurement_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    calculation_method VARCHAR(100), -- How the metric was calculated
    data_source VARCHAR(100), -- Source of the data
    confidence_level DECIMAL(5,2), -- Confidence in the metric (0-100)
    tags JSON, -- Additional metadata tags
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Indexes for performance
    INDEX idx_analytics_metrics_category (metric_category),
    INDEX idx_analytics_metrics_date (measurement_date),
    INDEX idx_analytics_metrics_department (department_id),
    INDEX idx_analytics_metrics_entity (entity_type, entity_id),
    INDEX idx_analytics_metrics_period (period_start, period_end)
);
```

#### **2. Report Templates Table**
```sql
-- Defines reusable report templates
CREATE TABLE report_templates (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Template identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) NOT NULL, -- 'dashboard', 'compliance', 'operational', 'custom', 'executive'
    category VARCHAR(50), -- 'quality', 'training', 'documents', 'organization', 'cross_module'
    
    -- Template configuration
    config JSON NOT NULL, -- Complete report configuration
    data_sources JSON, -- Array of data sources and queries
    parameters JSON, -- Configurable parameters
    layout JSON, -- Layout and visualization configuration
    
    -- Access control
    visibility VARCHAR(20) DEFAULT 'private', -- 'public', 'private', 'department', 'role'
    allowed_roles JSON, -- Array of role names that can access
    allowed_departments JSON, -- Array of department IDs that can access
    
    -- Template metadata
    version INTEGER DEFAULT 1,
    parent_template_id INTEGER REFERENCES report_templates(id),
    is_active BOOLEAN DEFAULT TRUE,
    is_system_template BOOLEAN DEFAULT FALSE, -- System vs user-created
    usage_count INTEGER DEFAULT 0,
    
    -- Audit fields
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    UNIQUE(name, created_by),
    INDEX idx_report_templates_type (report_type),
    INDEX idx_report_templates_category (category),
    INDEX idx_report_templates_active (is_active)
);
```

#### **3. Scheduled Reports Table**
```sql
-- Manages automated report generation and delivery
CREATE TABLE scheduled_reports (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Schedule identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_id INTEGER REFERENCES report_templates(id) NOT NULL,
    
    -- Scheduling configuration
    schedule_type VARCHAR(20) NOT NULL, -- 'cron', 'interval', 'manual'
    schedule_cron VARCHAR(50), -- Cron expression for complex scheduling
    schedule_interval INTEGER, -- Interval in minutes for simple scheduling
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Execution times
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    last_success TIMESTAMP WITH TIME ZONE,
    last_failure TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    
    -- Delivery configuration
    delivery_method VARCHAR(20) DEFAULT 'email', -- 'email', 'download', 'api', 'storage'
    recipients JSON, -- Array of email addresses or user IDs
    delivery_options JSON, -- Additional delivery configuration
    
    -- Report parameters
    parameters JSON, -- Parameters to pass to the report template
    output_format VARCHAR(10) DEFAULT 'pdf', -- 'pdf', 'excel', 'csv', 'json'
    
    -- Status and control
    is_active BOOLEAN DEFAULT TRUE,
    is_paused BOOLEAN DEFAULT FALSE,
    max_failures INTEGER DEFAULT 3,
    
    -- Audit fields
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    
    INDEX idx_scheduled_reports_next_run (next_run),
    INDEX idx_scheduled_reports_template (template_id),
    INDEX idx_scheduled_reports_active (is_active)
);
```

#### **4. Report Instances Table**
```sql
-- Tracks individual report generation instances
CREATE TABLE report_instances (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Instance identification
    template_id INTEGER REFERENCES report_templates(id) NOT NULL,
    scheduled_report_id INTEGER REFERENCES scheduled_reports(id), -- NULL for manual reports
    
    -- Generation details
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by INTEGER REFERENCES users(id),
    generation_time_ms INTEGER, -- Time taken to generate in milliseconds
    
    -- File information
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_size_bytes BIGINT,
    file_format VARCHAR(10) NOT NULL, -- 'pdf', 'excel', 'csv', 'json'
    file_hash VARCHAR(64), -- For integrity verification
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'generating', 'completed', 'failed', 'expired'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Report metadata
    parameters JSON, -- Parameters used for generation
    data_range JSON, -- Date range and scope of data included
    record_count INTEGER, -- Number of records in the report
    
    -- Access control
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    
    INDEX idx_report_instances_template (template_id),
    INDEX idx_report_instances_generated (generated_at),
    INDEX idx_report_instances_status (status)
);
```

#### **5. Dashboard Configurations Table**
```sql
-- Stores user and system dashboard configurations
CREATE TABLE dashboard_configurations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    
    -- Dashboard identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dashboard_type VARCHAR(50) NOT NULL, -- 'personal', 'department', 'executive', 'system'
    
    -- Configuration
    layout JSON NOT NULL, -- Dashboard layout and widget configuration
    refresh_interval INTEGER DEFAULT 300, -- Refresh interval in seconds
    auto_refresh BOOLEAN DEFAULT TRUE,
    
    -- Access control
    owner_id INTEGER REFERENCES users(id),
    department_id INTEGER REFERENCES departments(id),
    visibility VARCHAR(20) DEFAULT 'private', -- 'public', 'private', 'department'
    allowed_users JSON, -- Array of user IDs with access
    allowed_roles JSON, -- Array of role names with access
    
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
    is_deleted BOOLEAN DEFAULT FALSE,
    
    INDEX idx_dashboard_configs_owner (owner_id),
    INDEX idx_dashboard_configs_department (department_id),
    INDEX idx_dashboard_configs_type (dashboard_type)
);
```

#### **6. Analytics Cache Table**
```sql
-- Caches computed analytics results for performance
CREATE TABLE analytics_cache (
    id SERIAL PRIMARY KEY,
    
    -- Cache identification
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    cache_category VARCHAR(50), -- 'dashboard', 'report', 'metric'
    
    -- Cached data
    data JSON NOT NULL,
    data_hash VARCHAR(64),
    
    -- Cache metadata
    department_id INTEGER REFERENCES departments(id),
    user_id INTEGER REFERENCES users(id),
    parameters JSON, -- Parameters used to generate the cached data
    
    -- Cache control
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_hit TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_analytics_cache_key (cache_key),
    INDEX idx_analytics_cache_expires (expires_at),
    INDEX idx_analytics_cache_category (cache_category)
);
```

---

## 🔄 **Database Migration Implementation**

### **Migration File Structure:**
```
backend/database/migrations/
├── 003_analytics_foundation.sql
├── 004_analytics_indexes.sql
└── 005_analytics_sample_data.sql
```

Let's create the first migration file: