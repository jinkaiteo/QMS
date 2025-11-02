-- EDMS Phase 2: Workflow System Database Schema
-- Migration 011: Document Workflow Tables
-- Date: November 1, 2025

-- =====================================================
-- Document Workflows Table
-- Tracks the lifecycle of document approval processes
-- =====================================================
CREATE TABLE document_workflows (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() NOT NULL UNIQUE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    workflow_type VARCHAR(50) NOT NULL CHECK (workflow_type IN ('review', 'up_version', 'obsolete')),
    status VARCHAR(50) NOT NULL DEFAULT 'initiated' CHECK (status IN ('initiated', 'pending_review', 'pending_approval', 'approved', 'rejected', 'terminated')),
    initiated_by_id INTEGER NOT NULL REFERENCES users(id),
    current_step VARCHAR(50),
    reason TEXT, -- Reason for workflow initiation (especially for up-version and obsolete)
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    
    -- Indexes for performance
    INDEX idx_document_workflows_document_id (document_id),
    INDEX idx_document_workflows_status (status),
    INDEX idx_document_workflows_initiated_by (initiated_by_id),
    INDEX idx_document_workflows_type (workflow_type)
);

-- =====================================================
-- Workflow Steps Table  
-- Individual steps within a workflow (review, approve, etc.)
-- =====================================================
CREATE TABLE workflow_steps (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() NOT NULL UNIQUE,
    workflow_id INTEGER NOT NULL REFERENCES document_workflows(id) ON DELETE CASCADE,
    step_type VARCHAR(50) NOT NULL CHECK (step_type IN ('review', 'approve', 'notify')),
    step_order INTEGER NOT NULL DEFAULT 1,
    assigned_to_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'rejected', 'skipped')),
    
    -- Step details
    comments TEXT,
    decision VARCHAR(20) CHECK (decision IN ('approved', 'rejected')),
    due_date TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    
    -- Constraints
    UNIQUE(workflow_id, step_order),
    
    -- Indexes
    INDEX idx_workflow_steps_workflow_id (workflow_id),
    INDEX idx_workflow_steps_assigned_to (assigned_to_id),
    INDEX idx_workflow_steps_status (status),
    INDEX idx_workflow_steps_due_date (due_date)
);

-- =====================================================
-- Document Versions Table
-- Track file versions and metadata for each document
-- =====================================================
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() NOT NULL UNIQUE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL, -- e.g., "1.0", "1.1", "2.0"
    major_version INTEGER NOT NULL DEFAULT 1,
    minor_version INTEGER NOT NULL DEFAULT 0,
    
    -- File information
    file_path VARCHAR(500), -- Path in MinIO storage
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    checksum VARCHAR(64), -- SHA-256 for integrity
    
    -- Version metadata
    uploaded_by_id INTEGER NOT NULL REFERENCES users(id),
    upload_reason TEXT,
    is_current BOOLEAN DEFAULT FALSE,
    is_official BOOLEAN DEFAULT FALSE, -- TRUE for approved, signed versions
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    
    -- Constraints
    UNIQUE(document_id, version_number),
    CHECK (major_version > 0),
    CHECK (minor_version >= 0),
    
    -- Indexes
    INDEX idx_document_versions_document_id (document_id),
    INDEX idx_document_versions_current (document_id, is_current),
    INDEX idx_document_versions_official (document_id, is_official),
    INDEX idx_document_versions_uploaded_by (uploaded_by_id)
);

-- =====================================================
-- Document Dependencies Table
-- Track relationships between documents
-- =====================================================
CREATE TABLE document_dependencies (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() NOT NULL UNIQUE,
    parent_document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    dependent_document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'references' CHECK (dependency_type IN ('references', 'supersedes', 'implements', 'requires')),
    
    -- Metadata
    created_by_id INTEGER NOT NULL REFERENCES users(id),
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    UNIQUE(parent_document_id, dependent_document_id, dependency_type),
    CHECK (parent_document_id != dependent_document_id), -- Prevent self-reference
    
    -- Indexes
    INDEX idx_document_dependencies_parent (parent_document_id),
    INDEX idx_document_dependencies_dependent (dependent_document_id),
    INDEX idx_document_dependencies_type (dependency_type)
);

-- =====================================================
-- Document Roles Table
-- Role-based access control for documents
-- =====================================================
CREATE TABLE document_roles (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE, -- NULL for global roles
    role VARCHAR(50) NOT NULL CHECK (role IN ('viewer', 'author', 'reviewer', 'approver', 'admin')),
    
    -- Role metadata
    assigned_by_id INTEGER NOT NULL REFERENCES users(id),
    effective_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    effective_until TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    UNIQUE(user_id, document_id, role) WHERE document_id IS NOT NULL,
    UNIQUE(user_id, role) WHERE document_id IS NULL, -- Global roles
    
    -- Indexes
    INDEX idx_document_roles_user_id (user_id),
    INDEX idx_document_roles_document_id (document_id),
    INDEX idx_document_roles_role (role),
    INDEX idx_document_roles_effective (effective_from, effective_until)
);

-- =====================================================
-- Document Comments Table
-- Comments and annotations for workflow steps
-- =====================================================
CREATE TABLE document_comments (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() NOT NULL UNIQUE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    workflow_step_id INTEGER REFERENCES workflow_steps(id) ON DELETE CASCADE,
    parent_comment_id INTEGER REFERENCES document_comments(id) ON DELETE CASCADE,
    
    -- Comment content
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(50) DEFAULT 'general' CHECK (comment_type IN ('general', 'review', 'approval', 'rejection', 'clarification')),
    
    -- Author information
    author_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Indexes
    INDEX idx_document_comments_document_id (document_id),
    INDEX idx_document_comments_workflow_step (workflow_step_id),
    INDEX idx_document_comments_author (author_id),
    INDEX idx_document_comments_parent (parent_comment_id)
);

-- =====================================================
-- Add new columns to existing documents table
-- =====================================================
ALTER TABLE documents ADD COLUMN IF NOT EXISTS workflow_id INTEGER REFERENCES document_workflows(id);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS effective_date DATE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS review_due_date DATE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS superseded_by_id INTEGER REFERENCES documents(id);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS obsolete_date DATE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_source VARCHAR(50) DEFAULT 'original_digital' 
    CHECK (document_source IN ('original_digital', 'scanned_original', 'scanned_copy'));
ALTER TABLE documents ADD COLUMN IF NOT EXISTS revision_reason TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS current_version_id INTEGER REFERENCES document_versions(id);

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_documents_workflow_id ON documents(workflow_id);
CREATE INDEX IF NOT EXISTS idx_documents_effective_date ON documents(effective_date);
CREATE INDEX IF NOT EXISTS idx_documents_review_due_date ON documents(review_due_date);
CREATE INDEX IF NOT EXISTS idx_documents_superseded_by ON documents(superseded_by_id);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(document_source);

-- =====================================================
-- Workflow Status Update Triggers
-- Automatically update document status based on workflow
-- =====================================================
CREATE OR REPLACE FUNCTION update_document_status_from_workflow()
RETURNS TRIGGER AS $$
BEGIN
    -- Update document status based on workflow status
    IF NEW.status = 'approved' THEN
        UPDATE documents 
        SET status = 'approved',
            effective_date = COALESCE(effective_date, CURRENT_DATE),
            updated_at = NOW()
        WHERE id = NEW.document_id;
    ELSIF NEW.status = 'rejected' THEN
        UPDATE documents 
        SET status = 'draft',
            updated_at = NOW()
        WHERE id = NEW.document_id;
    ELSIF NEW.status = 'pending_review' THEN
        UPDATE documents 
        SET status = 'pending_review',
            updated_at = NOW()
        WHERE id = NEW.document_id;
    ELSIF NEW.status = 'pending_approval' THEN
        UPDATE documents 
        SET status = 'pending_approval',
            updated_at = NOW()
        WHERE id = NEW.document_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_document_status
    AFTER UPDATE OF status ON document_workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_document_status_from_workflow();

-- =====================================================
-- Version Management Triggers
-- Automatically manage current version flags
-- =====================================================
CREATE OR REPLACE FUNCTION manage_current_version()
RETURNS TRIGGER AS $$
BEGIN
    -- If setting a version as current, unset all others for this document
    IF NEW.is_current = TRUE THEN
        UPDATE document_versions 
        SET is_current = FALSE,
            updated_at = NOW()
        WHERE document_id = NEW.document_id 
          AND id != NEW.id;
          
        -- Update document current_version_id
        UPDATE documents 
        SET current_version_id = NEW.id,
            current_version = NEW.version_number,
            updated_at = NOW()
        WHERE id = NEW.document_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_manage_current_version
    AFTER INSERT OR UPDATE OF is_current ON document_versions
    FOR EACH ROW
    EXECUTE FUNCTION manage_current_version();

-- =====================================================
-- Sample Data for Testing
-- =====================================================

-- Create some document roles for existing users
INSERT INTO document_roles (user_id, role, assigned_by_id, notes) VALUES
(1, 'admin', 1, 'Global admin role for testing'),
(1, 'approver', 1, 'Global approver role for testing'),
(1, 'reviewer', 1, 'Global reviewer role for testing');

-- Create initial document versions for existing documents
INSERT INTO document_versions (document_id, version_number, major_version, minor_version, file_name, uploaded_by_id, is_current, upload_reason)
SELECT 
    id,
    '1.0',
    1,
    0,
    CONCAT(document_number, '_v1.0.docx'),
    created_by_id,
    TRUE,
    'Initial version upload'
FROM documents
WHERE id <= 10; -- Only for our 10 sample documents

-- Create some sample workflows for testing
INSERT INTO document_workflows (document_id, workflow_type, status, initiated_by_id, current_step, reason)
VALUES
(4, 'review', 'pending_review', 1, 'review', 'Initial review for draft policy document'),
(6, 'review', 'pending_approval', 1, 'approval', 'Review completed, pending final approval'),
(10, 'up_version', 'initiated', 1, 'revision', 'Minor updates to QRM manual based on feedback');

-- Create workflow steps for the sample workflows
INSERT INTO workflow_steps (workflow_id, step_type, step_order, assigned_to_id, status, due_date)
VALUES
-- Workflow 1 (Document 4): Pending Review
(1, 'review', 1, 1, 'pending', NOW() + INTERVAL '7 days'),
(1, 'approve', 2, 1, 'pending', NOW() + INTERVAL '14 days'),

-- Workflow 2 (Document 6): Pending Approval  
(2, 'review', 1, 1, 'completed', NOW() - INTERVAL '2 days'),
(2, 'approve', 2, 1, 'pending', NOW() + INTERVAL '5 days'),

-- Workflow 3 (Document 10): Up-version workflow
(3, 'review', 1, 1, 'pending', NOW() + INTERVAL '10 days'),
(3, 'approve', 2, 1, 'pending', NOW() + INTERVAL '17 days');

-- Add some sample comments
INSERT INTO document_comments (document_id, workflow_step_id, comment_text, comment_type, author_id)
VALUES
(4, 1, 'Please review the policy sections 3.2 and 4.1 for clarity and completeness.', 'review', 1),
(6, 1, 'Document reviewed and approved. Minor formatting suggestions included in attached notes.', 'review', 1),
(6, 2, 'Ready for final approval. All review comments have been addressed.', 'approval', 1);

-- Add some document dependencies
INSERT INTO document_dependencies (parent_document_id, dependent_document_id, dependency_type, created_by_id, notes)
VALUES
(1, 2, 'implements', 1, 'Document Control Procedure implements QMS Overview guidelines'),
(1, 3, 'references', 1, 'Quality Policy references QMS Overview principles'),
(5, 7, 'requires', 1, 'Deviation Report Form requires Equipment Calibration WI procedures');

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- Document workflow status view
CREATE OR REPLACE VIEW v_document_workflow_status AS
SELECT 
    d.id AS document_id,
    d.document_number,
    d.title,
    d.status AS document_status,
    dw.id AS workflow_id,
    dw.workflow_type,
    dw.status AS workflow_status,
    dw.current_step,
    dw.created_at AS workflow_started,
    u.username AS initiated_by,
    COUNT(ws.id) AS total_steps,
    COUNT(CASE WHEN ws.status = 'completed' THEN 1 END) AS completed_steps
FROM documents d
LEFT JOIN document_workflows dw ON d.workflow_id = dw.id
LEFT JOIN users u ON dw.initiated_by_id = u.id
LEFT JOIN workflow_steps ws ON dw.id = ws.workflow_id
WHERE d.is_deleted = FALSE
GROUP BY d.id, d.document_number, d.title, d.status, dw.id, dw.workflow_type, 
         dw.status, dw.current_step, dw.created_at, u.username;

-- User pending actions view  
CREATE OR REPLACE VIEW v_user_pending_actions AS
SELECT 
    ws.id AS step_id,
    ws.workflow_id,
    ws.step_type,
    ws.due_date,
    d.id AS document_id,
    d.document_number,
    d.title,
    u.id AS user_id,
    u.username,
    dw.workflow_type
FROM workflow_steps ws
JOIN document_workflows dw ON ws.workflow_id = dw.id
JOIN documents d ON dw.document_id = d.id
JOIN users u ON ws.assigned_to_id = u.id
WHERE ws.status = 'pending'
  AND d.is_deleted = FALSE
  AND dw.is_deleted = FALSE
ORDER BY ws.due_date ASC;

-- Document version history view
CREATE OR REPLACE VIEW v_document_version_history AS
SELECT 
    dv.id AS version_id,
    dv.document_id,
    d.document_number,
    d.title,
    dv.version_number,
    dv.major_version,
    dv.minor_version,
    dv.file_name,
    dv.file_size,
    dv.is_current,
    dv.is_official,
    dv.created_at AS version_created,
    u.username AS uploaded_by
FROM document_versions dv
JOIN documents d ON dv.document_id = d.id
JOIN users u ON dv.uploaded_by_id = u.id
WHERE dv.is_deleted = FALSE
ORDER BY dv.document_id, dv.major_version DESC, dv.minor_version DESC;

-- =====================================================
-- Constraints and Final Setup
-- =====================================================

-- Add foreign key constraint for workflow_id in documents
ALTER TABLE documents ADD CONSTRAINT fk_documents_workflow_id 
    FOREIGN KEY (workflow_id) REFERENCES document_workflows(id);

-- Add constraint for current_version_id in documents
ALTER TABLE documents ADD CONSTRAINT fk_documents_current_version_id 
    FOREIGN KEY (current_version_id) REFERENCES document_versions(id);

-- Create composite indexes for better query performance
CREATE INDEX idx_workflow_steps_workflow_status ON workflow_steps(workflow_id, status);
CREATE INDEX idx_document_workflows_document_status ON document_workflows(document_id, status);
CREATE INDEX idx_document_roles_user_document ON document_roles(user_id, document_id) WHERE is_deleted = FALSE;

-- Grant permissions (adjust based on your user setup)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO qms_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO qms_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO qms_user;

-- Add comments for documentation
COMMENT ON TABLE document_workflows IS 'Tracks document review, approval, and lifecycle workflows';
COMMENT ON TABLE workflow_steps IS 'Individual steps within document workflows (review, approve, etc.)';
COMMENT ON TABLE document_versions IS 'File versions and metadata for documents';
COMMENT ON TABLE document_dependencies IS 'Relationships and dependencies between documents';
COMMENT ON TABLE document_roles IS 'Role-based access control for documents';
COMMENT ON TABLE document_comments IS 'Comments and annotations for workflow steps';

-- Migration complete
SELECT 'EDMS Phase 2 database schema migration completed successfully' AS result;