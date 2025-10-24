-- QMS Default Data Insertion
-- Phase 1: Insert default organization, roles, and system admin

-- Insert default organization
INSERT INTO organizations (name, code, address, phone, email) VALUES 
('Default Pharmaceutical Company', 'DEFAULT', '123 Pharma Street, Drug City, DC 12345', '+1-555-0100', 'admin@pharma.com');

-- Insert default departments
INSERT INTO departments (organization_id, name, code, description) VALUES 
(1, 'Quality Assurance', 'QA', 'Quality assurance and compliance department'),
(1, 'Research & Development', 'RND', 'Research and development department'),
(1, 'Manufacturing', 'MFG', 'Manufacturing and production department'),
(1, 'Regulatory Affairs', 'REG', 'Regulatory affairs and submissions'),
(1, 'Information Technology', 'IT', 'Information technology and systems'),
(1, 'Laboratory', 'LAB', 'Analytical and quality control laboratory');

-- Insert system roles with comprehensive permissions
-- System Administration Roles
INSERT INTO roles (name, display_name, description, module, permissions) VALUES 
('system_admin', 'System Administrator', 'Full system access and administration', 'SYSTEM', 
 '["read", "write", "review", "approve", "admin", "user_management", "system_config", "audit_access"]'),

('system_user', 'System User', 'Basic system user with read access', 'SYSTEM', 
 '["read"]');

-- EDMS Roles
INSERT INTO roles (name, display_name, description, module, permissions) VALUES 
('edms_viewer', 'Document Viewer', 'View documents and basic information', 'EDMS', 
 '["read"]'),

('edms_author', 'Document Author', 'Create and edit documents', 'EDMS', 
 '["read", "write", "create_document", "edit_own_document"]'),

('edms_reviewer', 'Document Reviewer', 'Review and comment on documents', 'EDMS', 
 '["read", "write", "review", "comment", "review_workflow"]'),

('edms_approver', 'Document Approver', 'Approve documents for release', 'EDMS', 
 '["read", "write", "review", "approve", "approve_workflow", "sign_document"]'),

('edms_admin', 'EDMS Administrator', 'Full EDMS module administration', 'EDMS', 
 '["read", "write", "review", "approve", "admin", "manage_templates", "manage_categories", "system_config"]');

-- QRM Roles
INSERT INTO roles (name, display_name, description, module, permissions) VALUES 
('qrm_viewer', 'Quality Viewer', 'View quality records and reports', 'QRM', 
 '["read", "view_reports"]'),

('qrm_responsible', 'Quality Responsible Person', 'Create and manage quality events', 'QRM', 
 '["read", "write", "create_event", "update_own_event", "assign_capa"]'),

('qrm_reviewer', 'Quality Reviewer', 'Review quality events and investigations', 'QRM', 
 '["read", "write", "review", "review_event", "review_investigation", "review_capa"]'),

('qrm_approver', 'Quality Approver', 'Approve quality decisions and closures', 'QRM', 
 '["read", "write", "review", "approve", "approve_closure", "approve_capa", "sign_quality_record"]'),

('qrm_admin', 'QRM Administrator', 'Full QRM module administration', 'QRM', 
 '["read", "write", "review", "approve", "admin", "manage_workflows", "system_config"]');

-- TRM Roles
INSERT INTO roles (name, display_name, description, module, permissions) VALUES 
('trm_trainee', 'Trainee', 'Complete assigned training and view progress', 'TRM', 
 '["read", "complete_training", "view_own_records"]'),

('trm_coordinator', 'Training Coordinator', 'Manage training programs and assignments', 'TRM', 
 '["read", "write", "create_curriculum", "assign_training", "track_progress"]'),

('trm_trainer', 'Trainer', 'Conduct training and assess competency', 'TRM', 
 '["read", "write", "review", "conduct_training", "assess_competency", "approve_completion"]'),

('trm_manager', 'Training Manager', 'Approve training records and manage programs', 'TRM', 
 '["read", "write", "review", "approve", "approve_training", "manage_programs"]'),

('trm_admin', 'TRM Administrator', 'Full TRM module administration', 'TRM', 
 '["read", "write", "review", "approve", "admin", "system_config"]');

-- LIMS Roles
INSERT INTO roles (name, display_name, description, module, permissions) VALUES 
('lims_analyst', 'Laboratory Analyst', 'Perform tests and enter results', 'LIMS', 
 '["read", "write", "perform_test", "enter_results", "sample_handling"]'),

('lims_sample_manager', 'Sample Manager', 'Manage sample lifecycle and storage', 'LIMS', 
 '["read", "write", "sample_management", "inventory_management", "equipment_management"]'),

('lims_reviewer', 'Laboratory Reviewer', 'Review test results and methods', 'LIMS', 
 '["read", "write", "review", "review_results", "review_methods"]'),

('lims_director', 'Laboratory Director', 'Approve results and manage laboratory', 'LIMS', 
 '["read", "write", "review", "approve", "approve_results", "approve_coa", "sign_coa"]'),

('lims_admin', 'LIMS Administrator', 'Full LIMS module administration', 'LIMS', 
 '["read", "write", "review", "approve", "admin", "system_config"]');

-- Create system administrator user
INSERT INTO users (
    username, email, password_hash, first_name, last_name, 
    employee_id, organization_id, department_id, status
) VALUES (
    'sysadmin', 
    'sysadmin@pharma.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeGmB.xrJwtjrCqAG', -- password: Admin123!
    'System', 
    'Administrator',
    'SYS001',
    1,
    5, -- IT Department
    'active'
);

-- Create quality manager user
INSERT INTO users (
    username, email, password_hash, first_name, last_name, 
    employee_id, organization_id, department_id, status
) VALUES (
    'qmanager', 
    'qmanager@pharma.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeGmB.xrJwtjrCqAG', -- password: Admin123!
    'Quality', 
    'Manager',
    'QA001',
    1,
    1, -- QA Department
    'active'
);

-- Create test users for different roles
INSERT INTO users (
    username, email, password_hash, first_name, last_name, 
    employee_id, organization_id, department_id, status
) VALUES 
('jdoe', 'john.doe@pharma.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeGmB.xrJwtjrCqAG', 'John', 'Doe', 'EMP001', 1, 1, 'active'),
('msmith', 'mary.smith@pharma.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeGmB.xrJwtjrCqAG', 'Mary', 'Smith', 'EMP002', 1, 2, 'active'),
('bwilson', 'bob.wilson@pharma.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeGmB.xrJwtjrCqAG', 'Bob', 'Wilson', 'EMP003', 1, 6, 'active');

-- Assign roles to users
-- System Administrator
INSERT INTO user_roles (user_id, role_id, assigned_by) VALUES 
(1, 1, 1), -- sysadmin gets system_admin role
(1, 5, 1), -- sysadmin gets edms_admin role
(1, 10, 1), -- sysadmin gets qrm_admin role
(1, 15, 1), -- sysadmin gets trm_admin role
(1, 20, 1); -- sysadmin gets lims_admin role

-- Quality Manager
INSERT INTO user_roles (user_id, role_id, assigned_by) VALUES 
(2, 2, 1),  -- qmanager gets system_user role
(2, 4, 1),  -- qmanager gets edms_reviewer role
(2, 9, 1),  -- qmanager gets qrm_approver role
(2, 14, 1); -- qmanager gets trm_manager role

-- Test users
INSERT INTO user_roles (user_id, role_id, assigned_by) VALUES 
(3, 3, 1),  -- jdoe gets edms_author role
(3, 7, 1),  -- jdoe gets qrm_responsible role
(4, 4, 1),  -- msmith gets edms_reviewer role
(4, 8, 1),  -- msmith gets qrm_reviewer role
(5, 16, 1), -- bwilson gets lims_analyst role
(5, 11, 1); -- bwilson gets trm_trainee role

-- Insert default system settings
INSERT INTO system_settings (key, value, description) VALUES 
('app.name', '"QMS Pharmaceutical System"', 'Application name'),
('app.version', '"1.0.0"', 'Application version'),
('app.environment', '"development"', 'Current environment'),
('security.password_min_length', '8', 'Minimum password length'),
('security.password_complexity', 'true', 'Require password complexity'),
('security.session_timeout_minutes', '480', 'Session timeout in minutes (8 hours)'),
('security.max_failed_login_attempts', '5', 'Maximum failed login attempts before lockout'),
('security.account_lockout_duration_minutes', '30', 'Account lockout duration in minutes'),
('compliance.cfr_21_part_11_enabled', 'true', '21 CFR Part 11 compliance mode'),
('compliance.audit_retention_years', '7', 'Audit log retention period in years'),
('backup.daily_backup_enabled', 'true', 'Enable daily automatic backups'),
('backup.retention_days', '90', 'Backup retention period in days'),
('email.smtp_server', '""', 'SMTP server for email notifications'),
('email.smtp_port', '587', 'SMTP server port'),
('notifications.enabled', 'true', 'Enable system notifications'),
('documents.max_file_size_mb', '100', 'Maximum document file size in MB'),
('documents.allowed_extensions', '["pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt"]', 'Allowed document file extensions');

-- Insert document placeholders for EDMS
INSERT INTO system_settings (key, value, description) VALUES 
('edms.placeholders', '{
    "{{DOC_NUMBER}}": {"source": "document", "field": "document_number", "description": "Document number"},
    "{{DOC_TITLE}}": {"source": "document", "field": "title", "description": "Document title"},
    "{{DOC_VERSION}}": {"source": "version", "field": "version_number", "description": "Document version"},
    "{{DOC_AUTHOR}}": {"source": "user", "field": "full_name", "description": "Document author"},
    "{{DOC_REVIEWER}}": {"source": "reviewer", "field": "full_name", "description": "Document reviewer"},
    "{{DOC_APPROVER}}": {"source": "approver", "field": "full_name", "description": "Document approver"},
    "{{APPROVED_DATE}}": {"source": "version", "field": "approved_at", "format": "date", "description": "Approval date"},
    "{{EFFECTIVE_DATE}}": {"source": "version", "field": "effective_date", "format": "date", "description": "Effective date"},
    "{{DOWNLOAD_DATE}}": {"source": "system", "field": "current_datetime", "format": "datetime", "description": "Download timestamp"},
    "{{COMPANY_NAME}}": {"source": "organization", "field": "name", "description": "Company name"},
    "{{DOC_STATUS}}": {"source": "version", "field": "status", "description": "Document status"}
}', 'Document metadata placeholders for template replacement');

-- Log the initial setup in audit trail
SET app.current_user_id = '1';
SET app.client_ip = '127.0.0.1';

INSERT INTO audit_logs (
    user_id, username, action, table_name, record_id, 
    new_values, module, reason, is_system_action
) VALUES (
    1, 'sysadmin', 'CREATE', 'system_setup', 'initial',
    '{"message": "Initial QMS system setup completed", "version": "1.0.0", "timestamp": "' || CURRENT_TIMESTAMP || '"}',
    'SYSTEM', 'Initial system configuration and data setup', true
);

-- Create indexes for better performance on commonly queried fields
CREATE INDEX idx_users_full_name ON users((first_name || ' ' || last_name));
CREATE INDEX idx_user_roles_active ON user_roles(user_id, is_active) WHERE is_active = true;
CREATE INDEX idx_system_settings_key ON system_settings(key);

-- Update department manager references
UPDATE departments SET manager_id = 2 WHERE code = 'QA';  -- Quality Manager manages QA
UPDATE departments SET manager_id = 1 WHERE code = 'IT';  -- System Admin manages IT

COMMENT ON TABLE organizations IS 'Default pharmaceutical company setup';
COMMENT ON TABLE departments IS 'Standard pharmaceutical departments';
COMMENT ON TABLE users IS 'Initial system users with default credentials';
COMMENT ON TABLE roles IS 'Comprehensive role definitions for all QMS modules';
COMMENT ON TABLE system_settings IS 'System configuration and compliance settings';