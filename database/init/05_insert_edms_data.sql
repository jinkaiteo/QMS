-- EDMS Default Data Insertion - Phase 2
-- Insert default document types, categories, and configuration

-- Insert default document types
INSERT INTO document_types (name, code, prefix, description, is_controlled, retention_period_years) VALUES 
('Standard Operating Procedure', 'SOP', 'SOP', 'Standard Operating Procedures for pharmaceutical operations', true, 7),
('Policy', 'POL', 'POL', 'Company policies and guidelines', true, 10),
('Work Instruction', 'WI', 'WI', 'Detailed work instructions for specific tasks', true, 5),
('Form', 'FORM', 'FORM', 'Controlled forms and templates', true, 7),
('Manual', 'MAN', 'MAN', 'User manuals and technical documentation', true, 7),
('Report', 'RPT', 'RPT', 'Technical and compliance reports', false, 3),
('Specification', 'SPEC', 'SPEC', 'Product and material specifications', true, 10),
('Protocol', 'PROT', 'PROT', 'Test protocols and validation plans', true, 7),
('Certificate', 'CERT', 'CERT', 'Certificates of analysis and compliance', false, 5),
('Drawing', 'DWG', 'DWG', 'Technical drawings and schematics', true, 15);

-- Insert default document categories
INSERT INTO document_categories (name, code, description, color, icon) VALUES 
('Quality Management', 'QM', 'Quality management system documents', '#2E7D32', 'quality_check'),
('Manufacturing', 'MFG', 'Manufacturing and production documents', '#1976D2', 'precision_manufacturing'),
('Laboratory', 'LAB', 'Laboratory and analytical documents', '#7B1FA2', 'biotech'),
('Regulatory', 'REG', 'Regulatory compliance documents', '#D32F2F', 'gavel'),
('Safety', 'SAFETY', 'Health and safety documents', '#F57C00', 'health_and_safety'),
('Training', 'TRAIN', 'Training and competency documents', '#388E3C', 'school'),
('IT Systems', 'IT', 'Information technology documents', '#455A64', 'computer'),
('Maintenance', 'MAINT', 'Equipment maintenance documents', '#5D4037', 'build'),
('Validation', 'VAL', 'Validation and qualification documents', '#303F9F', 'verified'),
('General', 'GEN', 'General administrative documents', '#616161', 'description');

-- Insert subcategories
INSERT INTO document_categories (name, code, parent_id, description, color) VALUES 
-- Quality Management subcategories
('Quality Control', 'QC', 1, 'Quality control procedures and specifications', '#4CAF50'),
('Quality Assurance', 'QA', 1, 'Quality assurance procedures and policies', '#8BC34A'),
('Change Control', 'CC', 1, 'Change control procedures and forms', '#CDDC39'),
('Document Control', 'DC', 1, 'Document control procedures', '#FFC107'),

-- Manufacturing subcategories
('Production', 'PROD', 2, 'Production procedures and batch records', '#03A9F4'),
('Packaging', 'PACK', 2, 'Packaging procedures and specifications', '#00BCD4'),
('Equipment', 'EQUIP', 2, 'Manufacturing equipment procedures', '#009688'),

-- Laboratory subcategories
('Analytical Methods', 'AM', 3, 'Analytical test methods and procedures', '#9C27B0'),
('Stability Testing', 'STAB', 3, 'Stability testing protocols and procedures', '#673AB7'),
('Microbiological', 'MICRO', 3, 'Microbiological testing procedures', '#3F51B5'),

-- Regulatory subcategories
('Submissions', 'SUB', 4, 'Regulatory submission documents', '#F44336'),
('Inspections', 'INSP', 4, 'Inspection procedures and responses', '#E91E63'),
('Compliance', 'COMP', 4, 'Compliance monitoring procedures', '#9C27B0');

-- Insert sample document templates and placeholders
INSERT INTO system_settings (key, value, description) VALUES 
('edms.auto_numbering_enabled', 'true', 'Enable automatic document numbering'),
('edms.version_numbering_scheme', '"major.minor"', 'Document version numbering scheme'),
('edms.default_retention_years', '7', 'Default document retention period in years'),
('edms.require_review_approval', 'true', 'Require review and approval for controlled documents'),
('edms.max_parallel_workflows', '5', 'Maximum number of parallel workflows per document'),
('edms.notification_enabled', 'true', 'Enable workflow notifications'),
('edms.digital_signature_required', 'true', 'Require digital signatures for approved documents'),
('edms.backup_retention_days', '90', 'Document backup retention period in days');

-- Insert document workflow templates
INSERT INTO system_settings (key, value, description) VALUES 
('edms.workflow_templates', '{
    "sop_review": {
        "name": "SOP Review Workflow",
        "description": "Standard workflow for SOP review and approval",
        "steps": [
            {"step": 1, "name": "Technical Review", "role": "edms_reviewer", "required": true},
            {"step": 2, "name": "Quality Review", "role": "qrm_reviewer", "required": true},
            {"step": 3, "name": "Final Approval", "role": "edms_approver", "required": true}
        ],
        "auto_routing": true,
        "parallel_review": false
    },
    "policy_review": {
        "name": "Policy Review Workflow", 
        "description": "Standard workflow for policy review and approval",
        "steps": [
            {"step": 1, "name": "Department Review", "role": "edms_reviewer", "required": true},
            {"step": 2, "name": "Management Approval", "role": "edms_approver", "required": true}
        ],
        "auto_routing": true,
        "parallel_review": false
    },
    "form_review": {
        "name": "Form Review Workflow",
        "description": "Simplified workflow for form review",
        "steps": [
            {"step": 1, "name": "Form Review", "role": "edms_reviewer", "required": true},
            {"step": 2, "name": "Form Approval", "role": "edms_approver", "required": true}
        ],
        "auto_routing": true,
        "parallel_review": true
    }
}', 'Predefined workflow templates for different document types');

-- Set application context for audit logging
SET app.current_user_id = '1';
SET app.client_ip = '127.0.0.1';

-- Log the EDMS setup in audit trail
INSERT INTO audit_logs (
    user_id, username, action, table_name, record_id, 
    new_values, module, reason, is_system_action
) VALUES (
    1, 'sysadmin', 'CREATE', 'edms_setup', 'phase2',
    '{"message": "EDMS module setup completed", "document_types": 10, "categories": 20, "timestamp": "' || CURRENT_TIMESTAMP || '"}',
    'EDMS', 'Phase 2 EDMS module initialization', true
);

-- Create indexes for better performance on document searches
CREATE INDEX idx_documents_title_search ON documents USING gin(to_tsvector('english', title));
CREATE INDEX idx_documents_description_search ON documents USING gin(to_tsvector('english', description));
CREATE INDEX idx_documents_combined_search ON documents USING gin(
    to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, ''))
);

-- Create composite indexes for common query patterns
CREATE INDEX idx_documents_type_status ON documents(document_type_id, status);
CREATE INDEX idx_documents_category_status ON documents(category_id, status);
CREATE INDEX idx_documents_author_status ON documents(author_id, status);
CREATE INDEX idx_documents_created_status ON documents(created_at, status);

-- Comments for documentation
COMMENT ON TABLE document_types IS 'Phase 2: Document type definitions with numbering schemes';
COMMENT ON TABLE document_categories IS 'Phase 2: Hierarchical document categorization system';
COMMENT ON INDEX idx_documents_title_search IS 'Full-text search index for document titles';
COMMENT ON INDEX idx_documents_combined_search IS 'Combined full-text search index for titles and descriptions';