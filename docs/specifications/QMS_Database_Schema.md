# QMS System - Database Schema Design

## Table of Contents
1. [Core Database Design](#core-database-design)
2. [User Management Schema](#user-management-schema)
3. [EDMS Schema](#edms-schema)
4. [QRM Schema](#qrm-schema)
5. [TRM Schema](#trm-schema)
6. [LIMS Schema](#lims-schema)
7. [Audit Trail Schema](#audit-trail-schema)
8. [System Tables](#system-tables)

## Core Database Design

### Database Configuration
```sql
-- PostgreSQL 18 Configuration
-- Database: qms_prod
-- Character Set: UTF8
-- Collation: en_US.UTF-8
-- Time Zone: UTC

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
```

### Base Entity Design Pattern

```sql
-- Base table structure for all entities
-- All tables inherit from this pattern for consistency

CREATE TABLE base_entity (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER NOT NULL,
    version INTEGER DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by INTEGER
);

-- Trigger function for automatic updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

## User Management Schema

```sql
-- Organizations/Companies
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),
    regulatory_license VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Departments within organizations
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    description TEXT,
    manager_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    employee_id VARCHAR(50) UNIQUE,
    organization_id INTEGER REFERENCES organizations(id),
    department_id INTEGER REFERENCES departments(id),
    manager_id INTEGER REFERENCES users(id),
    phone VARCHAR(50),
    entra_id VARCHAR(255), -- Microsoft Entra ID
    digital_signature_cert TEXT, -- Base64 encoded certificate
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE,
    must_change_password BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Roles definition
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    module VARCHAR(50) NOT NULL, -- EDMS, QRM, TRM, LIMS, SYSTEM
    permissions JSONB NOT NULL, -- Array of permissions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- User-Role assignments
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    assigned_by INTEGER REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, role_id)
);

-- User sessions for tracking
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Password history for compliance
CREATE TABLE password_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_employee_id ON users(employee_id);
CREATE INDEX idx_users_organization ON users(organization_id);
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
```

## EDMS Schema

```sql
-- Document Types (Policy, Manual, Procedures, SOPs, Forms, Records)
CREATE TABLE document_types (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    code VARCHAR(20) UNIQUE NOT NULL,
    prefix VARCHAR(10), -- For document numbering
    workflow_type VARCHAR(50) DEFAULT 'standard',
    retention_period_years INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document Categories for better organization
CREATE TABLE document_categories (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES document_categories(id),
    path VARCHAR(500), -- Hierarchical path like "/Quality/SOPs/Laboratory"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Main documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    document_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    document_type_id INTEGER REFERENCES document_types(id),
    category_id INTEGER REFERENCES document_categories(id),
    source_type VARCHAR(50) NOT NULL, -- 'original_digital', 'scanned_original', 'scanned_copy'
    language VARCHAR(10) DEFAULT 'en',
    keywords TEXT[], -- Array of keywords for search
    tags JSONB, -- Flexible tagging system
    author_id INTEGER REFERENCES users(id) NOT NULL,
    current_version_id INTEGER, -- Points to current active version
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    confidentiality_level VARCHAR(20) DEFAULT 'internal', -- public, internal, confidential, restricted
    review_frequency_months INTEGER,
    next_review_date DATE,
    retention_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Document versions (for version control)
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL, -- e.g., "1.0", "1.1", "2.0"
    major_version INTEGER NOT NULL,
    minor_version INTEGER NOT NULL,
    revision_reason TEXT,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_mime_type VARCHAR(100),
    file_hash VARCHAR(128), -- SHA-256 hash for integrity
    page_count INTEGER,
    word_count INTEGER,
    author_id INTEGER REFERENCES users(id) NOT NULL,
    reviewer_id INTEGER REFERENCES users(id),
    approver_id INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    effective_date DATE,
    expiry_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    workflow_data JSONB, -- Store workflow state and history
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, version_number)
);

-- Document dependencies (references between documents)
CREATE TABLE document_dependencies (
    id SERIAL PRIMARY KEY,
    parent_document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    parent_version_id INTEGER REFERENCES document_versions(id),
    dependent_document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    dependent_version_id INTEGER REFERENCES document_versions(id),
    dependency_type VARCHAR(50) NOT NULL, -- 'references', 'supersedes', 'related', 'template'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    UNIQUE(parent_document_id, dependent_document_id, dependency_type)
);

-- Document workflow instances
CREATE TABLE document_workflows (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    document_version_id INTEGER REFERENCES document_versions(id) ON DELETE CASCADE,
    workflow_type VARCHAR(50) NOT NULL, -- 'review', 'up_version', 'obsolete'
    current_state VARCHAR(50) NOT NULL,
    initiated_by INTEGER REFERENCES users(id),
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancelled_by INTEGER REFERENCES users(id),
    cancellation_reason TEXT,
    due_date TIMESTAMP WITH TIME ZONE,
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    data JSONB, -- Store workflow-specific data
    is_active BOOLEAN DEFAULT TRUE
);

-- Document workflow steps/tasks
CREATE TABLE document_workflow_steps (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES document_workflows(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    assigned_to INTEGER REFERENCES users(id),
    assigned_role VARCHAR(100),
    due_date TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, skipped
    action_taken VARCHAR(100), -- approve, reject, request_changes
    comments TEXT,
    attachments JSONB, -- Array of attachment metadata
    data JSONB, -- Step-specific data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document reviews and comments
CREATE TABLE document_reviews (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    document_version_id INTEGER REFERENCES document_versions(id) ON DELETE CASCADE,
    workflow_step_id INTEGER REFERENCES document_workflow_steps(id),
    reviewer_id INTEGER REFERENCES users(id) NOT NULL,
    review_type VARCHAR(50) NOT NULL, -- 'technical', 'compliance', 'editorial'
    overall_decision VARCHAR(50), -- 'approve', 'approve_with_changes', 'reject'
    summary_comments TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_final BOOLEAN DEFAULT FALSE
);

-- Individual review comments (line-by-line feedback)
CREATE TABLE document_review_comments (
    id SERIAL PRIMARY KEY,
    review_id INTEGER REFERENCES document_reviews(id) ON DELETE CASCADE,
    page_number INTEGER,
    line_number INTEGER,
    section VARCHAR(100),
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(50), -- 'suggestion', 'error', 'question', 'critical'
    status VARCHAR(50) DEFAULT 'open', -- open, addressed, dismissed
    response TEXT,
    responded_by INTEGER REFERENCES users(id),
    responded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document signatures (digital signatures)
CREATE TABLE document_signatures (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    document_version_id INTEGER REFERENCES document_versions(id) ON DELETE CASCADE,
    signer_id INTEGER REFERENCES users(id) NOT NULL,
    signature_type VARCHAR(50) NOT NULL, -- 'author', 'reviewer', 'approver'
    signature_data JSONB NOT NULL, -- Digital signature metadata
    certificate_data TEXT, -- Base64 encoded certificate
    timestamp_authority VARCHAR(255),
    signature_hash VARCHAR(128),
    reason TEXT,
    location VARCHAR(100),
    signed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE
);

-- Document downloads tracking (for audit compliance)
CREATE TABLE document_downloads (
    id SERIAL PRIMARY KEY,
    document_version_id INTEGER REFERENCES document_versions(id) ON DELETE CASCADE,
    downloaded_by INTEGER REFERENCES users(id) NOT NULL,
    download_type VARCHAR(50) NOT NULL, -- 'original', 'annotated', 'official_pdf'
    file_name VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    download_reason VARCHAR(100),
    downloaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document metadata placeholders (for template replacement)
CREATE TABLE document_placeholders (
    id SERIAL PRIMARY KEY,
    placeholder VARCHAR(100) UNIQUE NOT NULL, -- e.g., {{DOC_NUMBER}}
    description VARCHAR(255),
    data_source VARCHAR(100), -- 'document', 'version', 'user', 'system'
    field_name VARCHAR(100), -- Field to extract value from
    format_pattern VARCHAR(100), -- Optional formatting
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for EDMS performance
CREATE INDEX idx_documents_number ON documents(document_number);
CREATE INDEX idx_documents_title ON documents USING GIN(to_tsvector('english', title));
CREATE INDEX idx_documents_type ON documents(document_type_id);
CREATE INDEX idx_documents_author ON documents(author_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_keywords ON documents USING GIN(keywords);
CREATE INDEX idx_document_versions_document ON document_versions(document_id);
CREATE INDEX idx_document_versions_status ON document_versions(status);
CREATE INDEX idx_document_workflows_document ON document_workflows(document_version_id);
CREATE INDEX idx_document_workflows_state ON document_workflows(current_state);
CREATE INDEX idx_document_downloads_user ON document_downloads(downloaded_by);
CREATE INDEX idx_document_downloads_date ON document_downloads(downloaded_at);

-- Add foreign key constraint after table creation
ALTER TABLE documents ADD CONSTRAINT fk_documents_current_version 
    FOREIGN KEY (current_version_id) REFERENCES document_versions(id);
```

## QRM Schema

```sql
-- Quality Event Types (Deviation, Investigation, CAPA, Change Control)
CREATE TABLE quality_event_types (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    severity_levels JSONB, -- Array of allowed severity levels
    default_timeline_days INTEGER,
    workflow_template JSONB, -- Default workflow configuration
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Main Quality Events table
CREATE TABLE quality_events (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    event_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    event_type_id INTEGER REFERENCES quality_event_types(id),
    severity VARCHAR(50) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    impact_area VARCHAR(100), -- 'product', 'process', 'system', 'safety'
    source VARCHAR(100), -- 'internal_audit', 'customer_complaint', 'supplier', 'self_inspection'
    location VARCHAR(255),
    department_id INTEGER REFERENCES departments(id),
    reported_by INTEGER REFERENCES users(id) NOT NULL,
    reported_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    occurred_date TIMESTAMP WITH TIME ZONE,
    discovered_date TIMESTAMP WITH TIME ZONE,
    responsible_person_id INTEGER REFERENCES users(id),
    assigned_reviewer_id INTEGER REFERENCES users(id),
    assigned_approver_id INTEGER REFERENCES users(id),
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, urgent
    due_date DATE,
    closure_date TIMESTAMP WITH TIME ZONE,
    closure_approved_by INTEGER REFERENCES users(id),
    regulatory_reportable BOOLEAN DEFAULT FALSE,
    regulatory_reported_date DATE,
    external_reference VARCHAR(100), -- Customer complaint number, etc.
    cost_impact DECIMAL(12,2),
    customer_impact BOOLEAN DEFAULT FALSE,
    product_affected TEXT,
    batch_lot_affected TEXT,
    tags JSONB,
    attachments JSONB, -- Array of attachment metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Deviations (escalated from quality events)
CREATE TABLE deviations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    deviation_number VARCHAR(100) UNIQUE NOT NULL,
    quality_event_id INTEGER REFERENCES quality_events(id),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    immediate_action TEXT,
    root_cause_analysis TEXT,
    corrective_action TEXT,
    preventive_action TEXT,
    investigation_summary TEXT,
    responsible_person_id INTEGER REFERENCES users(id) NOT NULL,
    reviewer_id INTEGER REFERENCES users(id),
    approver_id INTEGER REFERENCES users(id),
    target_completion_date DATE,
    actual_completion_date DATE,
    effectiveness_check_date DATE,
    effectiveness_verified BOOLEAN,
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    workflow_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Investigations (for unknown root causes)
CREATE TABLE investigations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    investigation_number VARCHAR(100) UNIQUE NOT NULL,
    quality_event_id INTEGER REFERENCES quality_events(id),
    title VARCHAR(500) NOT NULL,
    investigation_scope TEXT NOT NULL,
    methodology TEXT,
    timeline TEXT,
    findings TEXT,
    root_cause_analysis TEXT,
    contributing_factors TEXT,
    evidence_collected JSONB, -- Array of evidence items
    interviews_conducted JSONB, -- Array of interview records
    recommendations TEXT,
    responsible_person_id INTEGER REFERENCES users(id) NOT NULL,
    team_members JSONB, -- Array of team member IDs
    reviewer_id INTEGER REFERENCES users(id),
    approver_id INTEGER REFERENCES users(id),
    target_completion_date DATE,
    actual_completion_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    workflow_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- CAPA (Corrective and Preventive Actions)
CREATE TABLE capas (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    capa_number VARCHAR(100) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'quality_event', 'deviation', 'investigation'
    source_id INTEGER NOT NULL, -- ID of the source record
    title VARCHAR(500) NOT NULL,
    justification TEXT NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- 'corrective', 'preventive', 'both'
    action_description TEXT NOT NULL,
    implementation_plan TEXT,
    resources_required TEXT,
    responsible_person_id INTEGER REFERENCES users(id) NOT NULL,
    team_members JSONB, -- Array of team member IDs
    reviewer_id INTEGER REFERENCES users(id),
    approver_id INTEGER REFERENCES users(id),
    planned_start_date DATE,
    planned_completion_date DATE,
    actual_start_date DATE,
    actual_completion_date DATE,
    verification_method TEXT,
    verification_date DATE,
    verification_results TEXT,
    effectiveness_review_date DATE,
    effectiveness_verified BOOLEAN,
    effectiveness_comments TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, approved, in_progress, completed, verified
    cost_estimate DECIMAL(12,2),
    actual_cost DECIMAL(12,2),
    workflow_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Change Controls
CREATE TABLE change_controls (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    change_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    justification TEXT NOT NULL,
    change_type VARCHAR(100) NOT NULL, -- 'process', 'equipment', 'facility', 'documentation', 'system'
    change_category VARCHAR(50), -- 'minor', 'major', 'critical'
    impact_assessment TEXT,
    risk_assessment TEXT,
    validation_required BOOLEAN DEFAULT FALSE,
    validation_plan TEXT,
    implementation_plan TEXT,
    rollback_plan TEXT,
    testing_plan TEXT,
    training_required BOOLEAN DEFAULT FALSE,
    training_plan TEXT,
    documentation_updates JSONB, -- Array of documents to update
    affected_systems JSONB, -- Array of affected systems
    affected_products JSONB, -- Array of affected products
    initiator_id INTEGER REFERENCES users(id) NOT NULL,
    responsible_person_id INTEGER REFERENCES users(id),
    change_committee_members JSONB, -- Array of committee member IDs
    reviewer_id INTEGER REFERENCES users(id),
    approver_id INTEGER REFERENCES users(id),
    planned_implementation_date DATE,
    actual_implementation_date DATE,
    planned_completion_date DATE,
    actual_completion_date DATE,
    verification_date DATE,
    post_implementation_review_date DATE,
    effectiveness_verified BOOLEAN,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    priority VARCHAR(20) DEFAULT 'medium',
    cost_estimate DECIMAL(12,2),
    actual_cost DECIMAL(12,2),
    regulatory_impact BOOLEAN DEFAULT FALSE,
    customer_notification_required BOOLEAN DEFAULT FALSE,
    workflow_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Quality workflows (common workflow management for all QRM entities)
CREATE TABLE quality_workflows (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'quality_event', 'deviation', 'investigation', 'capa', 'change_control'
    entity_id INTEGER NOT NULL,
    workflow_type VARCHAR(50) NOT NULL,
    current_state VARCHAR(50) NOT NULL,
    initiated_by INTEGER REFERENCES users(id),
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    data JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- Quality workflow steps
CREATE TABLE quality_workflow_steps (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES quality_workflows(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    assigned_to INTEGER REFERENCES users(id),
    assigned_role VARCHAR(100),
    due_date TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending',
    action_taken VARCHAR(100),
    comments TEXT,
    attachments JSONB,
    escalated BOOLEAN DEFAULT FALSE,
    escalated_to INTEGER REFERENCES users(id),
    escalated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Quality notifications and alerts
CREATE TABLE quality_notifications (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    notification_type VARCHAR(50) NOT NULL, -- 'due_date', 'overdue', 'escalation', 'approval_needed'
    recipient_id INTEGER REFERENCES users(id) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    is_read BOOLEAN DEFAULT FALSE,
    is_acknowledged BOOLEAN DEFAULT FALSE
);

-- Create indexes for QRM performance
CREATE INDEX idx_quality_events_number ON quality_events(event_number);
CREATE INDEX idx_quality_events_reported_by ON quality_events(reported_by);
CREATE INDEX idx_quality_events_status ON quality_events(status);
CREATE INDEX idx_quality_events_date ON quality_events(reported_date);
CREATE INDEX idx_deviations_number ON deviations(deviation_number);
CREATE INDEX idx_deviations_quality_event ON deviations(quality_event_id);
CREATE INDEX idx_investigations_number ON investigations(investigation_number);
CREATE INDEX idx_capas_number ON capas(capa_number);
CREATE INDEX idx_capas_source ON capas(source_type, source_id);
CREATE INDEX idx_change_controls_number ON change_controls(change_number);
CREATE INDEX idx_quality_workflows_entity ON quality_workflows(entity_type, entity_id);
CREATE INDEX idx_quality_notifications_recipient ON quality_notifications(recipient_id);
CREATE INDEX idx_quality_notifications_read ON quality_notifications(is_read);
```