-- EDMS Phase 2: Workflow System Database Schema (Fixed)
-- Migration 011: Document Workflow Tables
-- Date: November 1, 2025

-- =====================================================
-- Document Workflows Table
-- =====================================================
CREATE TABLE IF NOT EXISTS document_workflows (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() NOT NULL UNIQUE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    workflow_type VARCHAR(50) NOT NULL CHECK (workflow_type IN ('review', 'up_version', 'obsolete')),
    status VARCHAR(50) NOT NULL DEFAULT 'initiated' CHECK (status IN ('initiated', 'pending_review', 'pending_approval', 'approved', 'rejected', 'terminated')),
    initiated_by_id INTEGER NOT NULL REFERENCES users(id),
    current_step VARCHAR(50),
    reason TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1
);

-- =====================================================
-- Workflow Steps Table  
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_steps (
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
    UNIQUE(workflow_id, step_order)
);

-- =====================================================
-- Document Versions Table
-- =====================================================
CREATE TABLE IF NOT EXISTS document_versions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() NOT NULL UNIQUE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL,
    major_version INTEGER NOT NULL DEFAULT 1,
    minor_version INTEGER NOT NULL DEFAULT 0,
    
    -- File information
    file_path VARCHAR(500),
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    checksum VARCHAR(64),
    
    -- Version metadata
    uploaded_by_id INTEGER NOT NULL REFERENCES users(id),
    upload_reason TEXT,
    is_current BOOLEAN DEFAULT FALSE,
    is_official BOOLEAN DEFAULT FALSE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    
    -- Constraints
    UNIQUE(document_id, version_number),
    CHECK (major_version > 0),
    CHECK (minor_version >= 0)
);

-- =====================================================
-- Document Dependencies Table
-- =====================================================
CREATE TABLE IF NOT EXISTS document_dependencies (
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
    CHECK (parent_document_id != dependent_document_id)
);

-- =====================================================
-- Document Roles Table
-- =====================================================
CREATE TABLE IF NOT EXISTS document_roles (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('viewer', 'author', 'reviewer', 'approver', 'admin')),
    
    -- Role metadata
    assigned_by_id INTEGER NOT NULL REFERENCES users(id),
    effective_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    effective_until TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- =====================================================
-- Document Comments Table
-- =====================================================
CREATE TABLE IF NOT EXISTS document_comments (
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
    is_deleted BOOLEAN DEFAULT FALSE
);

-- =====================================================
-- Add new columns to existing documents table
-- =====================================================
ALTER TABLE documents ADD COLUMN IF NOT EXISTS workflow_id INTEGER;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS revision_reason TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS current_version_id INTEGER;

-- =====================================================
-- Create Indexes (after tables are created)
-- =====================================================

-- Document Workflows indexes
CREATE INDEX IF NOT EXISTS idx_document_workflows_document_id ON document_workflows(document_id);
CREATE INDEX IF NOT EXISTS idx_document_workflows_status ON document_workflows(status);
CREATE INDEX IF NOT EXISTS idx_document_workflows_initiated_by ON document_workflows(initiated_by_id);
CREATE INDEX IF NOT EXISTS idx_document_workflows_type ON document_workflows(workflow_type);

-- Workflow Steps indexes
CREATE INDEX IF NOT EXISTS idx_workflow_steps_workflow_id ON workflow_steps(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_assigned_to ON workflow_steps(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_status ON workflow_steps(status);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_due_date ON workflow_steps(due_date);

-- Document Versions indexes
CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_document_versions_current ON document_versions(document_id, is_current);
CREATE INDEX IF NOT EXISTS idx_document_versions_official ON document_versions(document_id, is_official);
CREATE INDEX IF NOT EXISTS idx_document_versions_uploaded_by ON document_versions(uploaded_by_id);

-- Document Dependencies indexes
CREATE INDEX IF NOT EXISTS idx_document_dependencies_parent ON document_dependencies(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_document_dependencies_dependent ON document_dependencies(dependent_document_id);
CREATE INDEX IF NOT EXISTS idx_document_dependencies_type ON document_dependencies(dependency_type);

-- Document Roles indexes
CREATE INDEX IF NOT EXISTS idx_document_roles_user_id ON document_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_document_roles_document_id ON document_roles(document_id);
CREATE INDEX IF NOT EXISTS idx_document_roles_role ON document_roles(role);

-- Document Comments indexes
CREATE INDEX IF NOT EXISTS idx_document_comments_document_id ON document_comments(document_id);
CREATE INDEX IF NOT EXISTS idx_document_comments_workflow_step ON document_comments(workflow_step_id);
CREATE INDEX IF NOT EXISTS idx_document_comments_author ON document_comments(author_id);

-- Documents table new indexes
CREATE INDEX IF NOT EXISTS idx_documents_workflow_id ON documents(workflow_id);

-- =====================================================
-- Add Foreign Key Constraints (after tables exist)
-- =====================================================
DO $$
BEGIN
    -- Add workflow_id constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_documents_workflow_id') THEN
        ALTER TABLE documents ADD CONSTRAINT fk_documents_workflow_id 
            FOREIGN KEY (workflow_id) REFERENCES document_workflows(id);
    END IF;
    
    -- Add current_version_id constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_documents_current_version_id') THEN
        ALTER TABLE documents ADD CONSTRAINT fk_documents_current_version_id 
            FOREIGN KEY (current_version_id) REFERENCES document_versions(id);
    END IF;
END $$;

-- =====================================================
-- Create sample data for testing
-- =====================================================

-- Create document roles for existing users
INSERT INTO document_roles (user_id, role, assigned_by_id, notes) 
VALUES
(1, 'admin', 1, 'Global admin role for testing'),
(1, 'approver', 1, 'Global approver role for testing'),
(1, 'reviewer', 1, 'Global reviewer role for testing')
ON CONFLICT DO NOTHING;

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
WHERE id <= 10
AND NOT EXISTS (SELECT 1 FROM document_versions WHERE document_id = documents.id);

-- Create sample workflows for testing different statuses
INSERT INTO document_workflows (document_id, workflow_type, status, initiated_by_id, current_step, reason)
VALUES
(4, 'review', 'pending_review', 1, 'review', 'Initial review for draft policy document'),
(6, 'review', 'pending_approval', 1, 'approval', 'Review completed, pending final approval'),
(10, 'up_version', 'initiated', 1, 'revision', 'Minor updates to QRM manual based on feedback')
ON CONFLICT DO NOTHING;

-- Create workflow steps for the sample workflows
INSERT INTO workflow_steps (workflow_id, step_type, step_order, assigned_to_id, status, due_date)
SELECT 1, 'review', 1, 1, 'pending', NOW() + INTERVAL '7 days'
WHERE EXISTS (SELECT 1 FROM document_workflows WHERE id = 1)
AND NOT EXISTS (SELECT 1 FROM workflow_steps WHERE workflow_id = 1 AND step_order = 1);

INSERT INTO workflow_steps (workflow_id, step_type, step_order, assigned_to_id, status, due_date)
SELECT 1, 'approve', 2, 1, 'pending', NOW() + INTERVAL '14 days'
WHERE EXISTS (SELECT 1 FROM document_workflows WHERE id = 1)
AND NOT EXISTS (SELECT 1 FROM workflow_steps WHERE workflow_id = 1 AND step_order = 2);

-- Similar for other workflows...
INSERT INTO workflow_steps (workflow_id, step_type, step_order, assigned_to_id, status, due_date)
SELECT 2, 'review', 1, 1, 'completed', NOW() - INTERVAL '2 days'
WHERE EXISTS (SELECT 1 FROM document_workflows WHERE id = 2)
AND NOT EXISTS (SELECT 1 FROM workflow_steps WHERE workflow_id = 2 AND step_order = 1);

INSERT INTO workflow_steps (workflow_id, step_type, step_order, assigned_to_id, status, due_date)
SELECT 2, 'approve', 2, 1, 'pending', NOW() + INTERVAL '5 days'
WHERE EXISTS (SELECT 1 FROM document_workflows WHERE id = 2)
AND NOT EXISTS (SELECT 1 FROM workflow_steps WHERE workflow_id = 2 AND step_order = 2);

-- Add sample comments
INSERT INTO document_comments (document_id, workflow_step_id, comment_text, comment_type, author_id)
SELECT 4, 1, 'Please review the policy sections 3.2 and 4.1 for clarity and completeness.', 'review', 1
WHERE EXISTS (SELECT 1 FROM workflow_steps WHERE id = 1)
AND NOT EXISTS (SELECT 1 FROM document_comments WHERE document_id = 4 AND workflow_step_id = 1);

-- Add sample dependencies
INSERT INTO document_dependencies (parent_document_id, dependent_document_id, dependency_type, created_by_id, notes)
VALUES
(1, 2, 'implements', 1, 'Document Control Procedure implements QMS Overview guidelines'),
(1, 3, 'references', 1, 'Quality Policy references QMS Overview principles')
ON CONFLICT DO NOTHING;

-- Update some documents to link to workflows
UPDATE documents 
SET workflow_id = 1, 
    status = 'pending_review'
WHERE id = 4 AND workflow_id IS NULL;

UPDATE documents 
SET workflow_id = 2, 
    status = 'pending_approval'
WHERE id = 6 AND workflow_id IS NULL;

UPDATE documents 
SET workflow_id = 3, 
    status = 'draft'
WHERE id = 10 AND workflow_id IS NULL;

-- Update current_version_id for documents
UPDATE documents 
SET current_version_id = dv.id,
    current_version = '1.0'
FROM document_versions dv 
WHERE documents.id = dv.document_id 
AND dv.is_current = TRUE 
AND documents.current_version_id IS NULL;

-- =====================================================
-- Create useful views
-- =====================================================

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
LEFT JOIN workflow_steps ws ON dw.id = ws.workflow_id AND ws.is_deleted = FALSE
WHERE d.is_deleted = FALSE
GROUP BY d.id, d.document_number, d.title, d.status, dw.id, dw.workflow_type, 
         dw.status, dw.current_step, dw.created_at, u.username;

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
  AND ws.is_deleted = FALSE
ORDER BY ws.due_date ASC;

-- Migration complete
SELECT 'EDMS Phase 2 database schema migration completed successfully' AS result,
       COUNT(*) AS total_workflow_tables
FROM information_schema.tables 
WHERE table_name IN ('document_workflows', 'workflow_steps', 'document_versions', 'document_dependencies', 'document_roles', 'document_comments');