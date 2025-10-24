-- EDMS Tables Creation - Phase 2
-- Electronic Document Management System tables

-- Document types and categories
CREATE TABLE document_types (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    prefix VARCHAR(10), -- For document numbering (e.g., SOP-, POL-)
    description TEXT,
    template_file_path VARCHAR(500),
    is_controlled BOOLEAN DEFAULT TRUE,
    retention_period_years INTEGER DEFAULT 7,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE document_categories (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES document_categories(id),
    description TEXT,
    color VARCHAR(7), -- Hex color code
    icon VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE
);

-- Core documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    document_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    document_type_id INTEGER REFERENCES document_types(id) NOT NULL,
    category_id INTEGER REFERENCES document_categories(id),
    source_type VARCHAR(50) DEFAULT 'internal', -- internal, external, imported
    author_id INTEGER REFERENCES users(id) NOT NULL,
    owner_id INTEGER REFERENCES users(id),
    current_version_id INTEGER, -- References document_versions(id)
    status document_status DEFAULT 'draft',
    keywords TEXT[], -- Array of keywords for search
    tags TEXT[], -- Array of tags
    is_template BOOLEAN DEFAULT FALSE,
    is_controlled BOOLEAN DEFAULT TRUE,
    confidentiality_level VARCHAR(50) DEFAULT 'internal', -- public, internal, confidential, restricted
    next_review_date DATE,
    superseded_by INTEGER REFERENCES documents(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Document versions for complete versioning
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    document_id INTEGER REFERENCES documents(id) NOT NULL,
    version_number VARCHAR(20) NOT NULL, -- e.g., "1.0", "2.1", "3.0-DRAFT"
    major_version INTEGER NOT NULL,
    minor_version INTEGER NOT NULL,
    is_draft BOOLEAN DEFAULT TRUE,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash VARCHAR(128) NOT NULL, -- SHA-256 hash
    file_mime_type VARCHAR(100) NOT NULL,
    page_count INTEGER,
    word_count INTEGER,
    author_id INTEGER REFERENCES users(id) NOT NULL,
    reviewer_id INTEGER REFERENCES users(id),
    approver_id INTEGER REFERENCES users(id),
    change_summary TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    effective_date DATE,
    expiry_date DATE,
    status document_status DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    UNIQUE(document_id, version_number)
);

-- Add foreign key for current version
ALTER TABLE documents ADD CONSTRAINT fk_documents_current_version 
    FOREIGN KEY (current_version_id) REFERENCES document_versions(id);

-- Document workflows for review/approval processes
CREATE TABLE document_workflows (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    document_version_id INTEGER REFERENCES document_versions(id) NOT NULL,
    workflow_type VARCHAR(50) NOT NULL, -- review, approval, change_control
    workflow_name VARCHAR(255),
    current_state workflow_state DEFAULT 'pending',
    initiated_by INTEGER REFERENCES users(id) NOT NULL,
    assigned_to INTEGER REFERENCES users(id),
    due_date DATE,
    priority INTEGER DEFAULT 3, -- 1=High, 2=Medium, 3=Low
    comments TEXT,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Workflow steps for complex approval processes
CREATE TABLE workflow_steps (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    workflow_id INTEGER REFERENCES document_workflows(id) NOT NULL,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    assigned_to INTEGER REFERENCES users(id) NOT NULL,
    required BOOLEAN DEFAULT TRUE,
    completed_by INTEGER REFERENCES users(id),
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date DATE,
    comments TEXT,
    status workflow_state DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Digital signatures for electronic records
CREATE TABLE digital_signatures (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    document_version_id INTEGER REFERENCES document_versions(id) NOT NULL,
    signer_id INTEGER REFERENCES users(id) NOT NULL,
    signature_type signature_type NOT NULL,
    signature_meaning VARCHAR(255) NOT NULL, -- e.g., "Approved by", "Reviewed by"
    signature_hash VARCHAR(512) NOT NULL, -- Digital signature hash
    certificate_hash VARCHAR(256), -- Certificate fingerprint
    certificate_subject VARCHAR(500),
    timestamp_authority_response TEXT, -- TSA response for long-term validity
    signed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document relationships (dependencies, references)
CREATE TABLE document_relationships (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    parent_document_id INTEGER REFERENCES documents(id) NOT NULL,
    child_document_id INTEGER REFERENCES documents(id) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- references, depends_on, supersedes, related_to
    description TEXT,
    created_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(parent_document_id, child_document_id, relationship_type)
);

-- Document access permissions
CREATE TABLE document_permissions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    role_id INTEGER REFERENCES roles(id),
    permission_type VARCHAR(50) NOT NULL, -- read, write, review, approve, download
    granted_by INTEGER REFERENCES users(id) NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    CHECK ((user_id IS NOT NULL AND role_id IS NULL) OR (user_id IS NULL AND role_id IS NOT NULL))
);

-- Document comments and annotations
CREATE TABLE document_comments (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    document_version_id INTEGER REFERENCES document_versions(id) NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    parent_comment_id INTEGER REFERENCES document_comments(id),
    content TEXT NOT NULL,
    page_number INTEGER,
    position_x FLOAT,
    position_y FLOAT,
    highlight_text TEXT,
    comment_type VARCHAR(50) DEFAULT 'general', -- general, review, approval, suggestion
    status VARCHAR(50) DEFAULT 'open', -- open, addressed, resolved, dismissed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Create indexes for performance
CREATE INDEX idx_documents_number ON documents(document_number);
CREATE INDEX idx_documents_title ON documents USING gin(to_tsvector('english', title));
CREATE INDEX idx_documents_type ON documents(document_type_id);
CREATE INDEX idx_documents_category ON documents(category_id);
CREATE INDEX idx_documents_author ON documents(author_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_keywords ON documents USING gin(keywords);
CREATE INDEX idx_documents_tags ON documents USING gin(tags);
CREATE INDEX idx_documents_created ON documents(created_at);

CREATE INDEX idx_document_versions_document ON document_versions(document_id);
CREATE INDEX idx_document_versions_version ON document_versions(document_id, major_version, minor_version);
CREATE INDEX idx_document_versions_hash ON document_versions(file_hash);
CREATE INDEX idx_document_versions_status ON document_versions(status);

CREATE INDEX idx_workflows_document_version ON document_workflows(document_version_id);
CREATE INDEX idx_workflows_assigned ON document_workflows(assigned_to);
CREATE INDEX idx_workflows_state ON document_workflows(current_state);
CREATE INDEX idx_workflows_due_date ON document_workflows(due_date);

CREATE INDEX idx_workflow_steps_workflow ON workflow_steps(workflow_id);
CREATE INDEX idx_workflow_steps_assigned ON workflow_steps(assigned_to);
CREATE INDEX idx_workflow_steps_status ON workflow_steps(status);

CREATE INDEX idx_signatures_document_version ON digital_signatures(document_version_id);
CREATE INDEX idx_signatures_signer ON digital_signatures(signer_id);
CREATE INDEX idx_signatures_signed_at ON digital_signatures(signed_at);

CREATE INDEX idx_relationships_parent ON document_relationships(parent_document_id);
CREATE INDEX idx_relationships_child ON document_relationships(child_document_id);

CREATE INDEX idx_permissions_document ON document_permissions(document_id);
CREATE INDEX idx_permissions_user ON document_permissions(user_id);
CREATE INDEX idx_permissions_role ON document_permissions(role_id);

CREATE INDEX idx_comments_document_version ON document_comments(document_version_id);
CREATE INDEX idx_comments_user ON document_comments(user_id);
CREATE INDEX idx_comments_status ON document_comments(status);

-- Add triggers for automatic timestamp updates
CREATE TRIGGER update_document_types_updated_at 
    BEFORE UPDATE ON document_types 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_categories_updated_at 
    BEFORE UPDATE ON document_categories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_versions_updated_at 
    BEFORE UPDATE ON document_versions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_workflows_updated_at 
    BEFORE UPDATE ON document_workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_comments_updated_at 
    BEFORE UPDATE ON document_comments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add audit triggers for compliance
CREATE TRIGGER audit_documents_trigger
    AFTER INSERT OR UPDATE OR DELETE ON documents
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_document_versions_trigger
    AFTER INSERT OR UPDATE OR DELETE ON document_versions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_document_workflows_trigger
    AFTER INSERT OR UPDATE OR DELETE ON document_workflows
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_digital_signatures_trigger
    AFTER INSERT OR UPDATE OR DELETE ON digital_signatures
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_document_permissions_trigger
    AFTER INSERT OR UPDATE OR DELETE ON document_permissions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO qms_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO qms_user;

-- Comments for documentation
COMMENT ON TABLE document_types IS 'Document type definitions (SOP, Policy, Manual, etc.)';
COMMENT ON TABLE document_categories IS 'Hierarchical document categorization';
COMMENT ON TABLE documents IS 'Main document registry with metadata';
COMMENT ON TABLE document_versions IS 'Document version history with file storage';
COMMENT ON TABLE document_workflows IS 'Document review and approval workflows';
COMMENT ON TABLE workflow_steps IS 'Individual steps in document workflows';
COMMENT ON TABLE digital_signatures IS 'Electronic signatures for documents';
COMMENT ON TABLE document_relationships IS 'Document interdependencies and references';
COMMENT ON TABLE document_permissions IS 'Access control for documents';
COMMENT ON TABLE document_comments IS 'Review comments and annotations';

COMMENT ON COLUMN documents.confidentiality_level IS 'Document access classification';
COMMENT ON COLUMN document_versions.file_hash IS 'SHA-256 hash for integrity verification';
COMMENT ON COLUMN digital_signatures.signature_hash IS 'Digital signature for non-repudiation';
COMMENT ON COLUMN digital_signatures.timestamp_authority_response IS 'RFC 3161 timestamp for long-term validity';