-- ============================================================================
-- Training Management System (TMS) Database Schema
-- QMS Platform v3.0 - Production Database Setup
-- ============================================================================

-- Enable UUID extension for better primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable audit trigger extension for change tracking
CREATE EXTENSION IF NOT EXISTS "audit";

-- ============================================================================
-- ENUMS AND TYPES
-- ============================================================================

-- Training program types
CREATE TYPE training_type AS ENUM (
    'mandatory',
    'compliance', 
    'safety',
    'technical',
    'leadership'
);

-- Training status for programs
CREATE TYPE program_status AS ENUM (
    'draft',
    'active',
    'inactive',
    'archived',
    'under_review'
);

-- Training assignment status
CREATE TYPE assignment_status AS ENUM (
    'assigned',
    'not_started', 
    'in_progress',
    'completed',
    'overdue',
    'cancelled',
    'failed'
);

-- Document types for EDMS integration
CREATE TYPE document_type AS ENUM (
    'SOP',
    'Form',
    'Policy', 
    'Manual',
    'Certificate',
    'Work_Instruction'
);

-- Document categories
CREATE TYPE document_category AS ENUM (
    'Reference_Material',
    'Training_Form',
    'Certificate_Template'
);

-- ============================================================================
-- CORE TRAINING TABLES
-- ============================================================================

-- Training Programs Table
CREATE TABLE training_programs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    type training_type NOT NULL,
    duration INTEGER NOT NULL CHECK (duration > 0), -- in hours
    passing_score INTEGER DEFAULT 70 CHECK (passing_score BETWEEN 0 AND 100),
    validity_period INTEGER DEFAULT 12 CHECK (validity_period > 0), -- in months
    status program_status DEFAULT 'draft',
    
    -- Metadata
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    retired_at TIMESTAMP WITH TIME ZONE,
    retirement_reason TEXT,
    
    -- Version control
    version INTEGER DEFAULT 1,
    supersedes_id UUID REFERENCES training_programs(id),
    
    -- Constraints
    CONSTRAINT valid_title CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT valid_duration CHECK (duration BETWEEN 1 AND 168) -- max 1 week
);

-- Training Program Modules (for future phase 2)
CREATE TABLE training_modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID NOT NULL REFERENCES training_programs(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    sequence_order INTEGER NOT NULL,
    duration INTEGER NOT NULL CHECK (duration > 0), -- in minutes
    content_type VARCHAR(50) DEFAULT 'document',
    is_required BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(program_id, sequence_order),
    CONSTRAINT valid_module_title CHECK (LENGTH(TRIM(title)) > 0)
);

-- Training Assignments Table
CREATE TABLE training_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID NOT NULL REFERENCES training_programs(id),
    employee_id VARCHAR(50) NOT NULL, -- Reference to users table
    
    -- Assignment details
    assigned_by VARCHAR(100) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status assignment_status DEFAULT 'assigned',
    
    -- Progress tracking
    progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Assessment results
    score INTEGER CHECK (score BETWEEN 0 AND 100),
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Additional information
    notes TEXT,
    completion_certificate_id VARCHAR(100), -- Reference to generated certificate
    
    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_due_date CHECK (due_date > assigned_at),
    CONSTRAINT valid_completion CHECK (
        (status = 'completed' AND completed_at IS NOT NULL) OR
        (status != 'completed' AND completed_at IS NULL)
    ),
    CONSTRAINT valid_score CHECK (
        (status = 'completed' AND score IS NOT NULL) OR
        (status != 'completed')
    ),
    CONSTRAINT valid_progress_completion CHECK (
        (status = 'completed' AND progress = 100) OR
        (status != 'completed')
    )
);

-- Training Documents (EDMS Integration)
CREATE TABLE training_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID NOT NULL REFERENCES training_programs(id) ON DELETE CASCADE,
    
    -- Document references
    document_id VARCHAR(100) NOT NULL, -- EDMS document ID
    document_title VARCHAR(255) NOT NULL,
    document_type document_type NOT NULL,
    category document_category NOT NULL,
    document_version VARCHAR(20),
    
    -- Relationship
    is_required BOOLEAN DEFAULT false,
    sequence_order INTEGER DEFAULT 0,
    
    -- Metadata
    linked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    linked_by VARCHAR(100) NOT NULL,
    
    UNIQUE(program_id, document_id),
    CONSTRAINT valid_document_title CHECK (LENGTH(TRIM(document_title)) > 0)
);

-- Training Prerequisites (for future phase 2)
CREATE TABLE training_prerequisites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID NOT NULL REFERENCES training_programs(id) ON DELETE CASCADE,
    prerequisite_program_id UUID NOT NULL REFERENCES training_programs(id),
    is_required BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(program_id, prerequisite_program_id),
    CONSTRAINT no_self_prerequisite CHECK (program_id != prerequisite_program_id)
);

-- ============================================================================
-- AUDIT AND TRACKING TABLES
-- ============================================================================

-- Training Assignment History (audit trail)
CREATE TABLE training_assignment_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID NOT NULL REFERENCES training_assignments(id),
    
    -- Change tracking
    field_name VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,
    
    -- Who and when
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Context
    client_ip INET,
    user_agent TEXT
);

-- Training Session Logs (detailed activity tracking)
CREATE TABLE training_session_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID NOT NULL REFERENCES training_assignments(id),
    
    -- Session details
    session_start TIMESTAMP WITH TIME ZONE NOT NULL,
    session_end TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Progress tracking
    modules_completed INTEGER DEFAULT 0,
    last_module_id UUID REFERENCES training_modules(id),
    progress_snapshot INTEGER DEFAULT 0,
    
    -- Technical details
    client_ip INET,
    user_agent TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- DASHBOARD AND STATISTICS VIEWS
-- ============================================================================

-- Training Dashboard Statistics View
CREATE VIEW training_dashboard_stats AS
SELECT 
    -- Program counts
    (SELECT COUNT(*) FROM training_programs WHERE status = 'active') as total_programs,
    
    -- Assignment counts
    (SELECT COUNT(*) 
     FROM training_assignments 
     WHERE status IN ('assigned', 'not_started', 'in_progress')) as active_assignments,
    
    -- Monthly completions
    (SELECT COUNT(*) 
     FROM training_assignments 
     WHERE status = 'completed' 
     AND completed_at >= DATE_TRUNC('month', CURRENT_DATE)) as completed_this_month,
    
    -- Overdue trainings
    (SELECT COUNT(*) 
     FROM training_assignments 
     WHERE status IN ('assigned', 'not_started', 'in_progress') 
     AND due_date < NOW()) as overdue_trainings,
    
    -- Compliance rate calculation
    CASE 
        WHEN (SELECT COUNT(*) FROM training_assignments WHERE due_date <= NOW()) = 0 THEN 100.0
        ELSE ROUND(
            (SELECT COUNT(*) FROM training_assignments 
             WHERE status = 'completed' 
             AND due_date <= NOW() 
             AND completed_at <= due_date) * 100.0 / 
            (SELECT COUNT(*) FROM training_assignments WHERE due_date <= NOW()), 
            1
        )
    END as compliance_rate;

-- Program Statistics View
CREATE VIEW program_statistics AS
SELECT 
    tp.id,
    tp.title,
    tp.type,
    tp.status,
    COUNT(ta.id) as total_assignments,
    COUNT(CASE WHEN ta.status = 'completed' THEN 1 END) as completed_assignments,
    COUNT(CASE WHEN ta.status IN ('assigned', 'not_started', 'in_progress') THEN 1 END) as active_assignments,
    COUNT(CASE WHEN ta.status IN ('assigned', 'not_started', 'in_progress') AND ta.due_date < NOW() THEN 1 END) as overdue_assignments,
    ROUND(AVG(CASE WHEN ta.status = 'completed' THEN ta.score END), 1) as average_score,
    tp.created_at,
    tp.updated_at
FROM training_programs tp
LEFT JOIN training_assignments ta ON tp.id = ta.program_id
GROUP BY tp.id, tp.title, tp.type, tp.status, tp.created_at, tp.updated_at;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Training Programs Indexes
CREATE INDEX idx_training_programs_status ON training_programs(status);
CREATE INDEX idx_training_programs_type ON training_programs(type);
CREATE INDEX idx_training_programs_created_by ON training_programs(created_by);
CREATE INDEX idx_training_programs_created_at ON training_programs(created_at);

-- Training Assignments Indexes
CREATE INDEX idx_training_assignments_program_id ON training_assignments(program_id);
CREATE INDEX idx_training_assignments_employee_id ON training_assignments(employee_id);
CREATE INDEX idx_training_assignments_status ON training_assignments(status);
CREATE INDEX idx_training_assignments_due_date ON training_assignments(due_date);
CREATE INDEX idx_training_assignments_assigned_at ON training_assignments(assigned_at);
CREATE INDEX idx_training_assignments_completed_at ON training_assignments(completed_at);

-- Composite indexes for common queries
CREATE INDEX idx_assignments_employee_status ON training_assignments(employee_id, status);
CREATE INDEX idx_assignments_program_status ON training_assignments(program_id, status);
CREATE INDEX idx_assignments_due_overdue ON training_assignments(due_date, status) 
WHERE status IN ('assigned', 'not_started', 'in_progress');

-- Training Documents Indexes
CREATE INDEX idx_training_documents_program_id ON training_documents(program_id);
CREATE INDEX idx_training_documents_document_id ON training_documents(document_id);
CREATE INDEX idx_training_documents_type ON training_documents(document_type);

-- ============================================================================
-- TRIGGERS FOR AUTOMATION
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_training_programs_updated_at 
    BEFORE UPDATE ON training_programs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_training_assignments_updated_at 
    BEFORE UPDATE ON training_assignments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Assignment status change trigger for history
CREATE OR REPLACE FUNCTION log_assignment_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Log status changes
    IF OLD.status != NEW.status THEN
        INSERT INTO training_assignment_history (
            assignment_id, field_name, old_value, new_value, 
            changed_by, change_reason
        ) VALUES (
            NEW.id, 'status', OLD.status::text, NEW.status::text,
            NEW.updated_by, 'Status change'
        );
    END IF;
    
    -- Log progress changes
    IF OLD.progress != NEW.progress THEN
        INSERT INTO training_assignment_history (
            assignment_id, field_name, old_value, new_value, 
            changed_by, change_reason
        ) VALUES (
            NEW.id, 'progress', OLD.progress::text, NEW.progress::text,
            NEW.updated_by, 'Progress update'
        );
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER log_training_assignment_changes 
    AFTER UPDATE ON training_assignments 
    FOR EACH ROW EXECUTE FUNCTION log_assignment_changes();

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample training programs
INSERT INTO training_programs (
    title, description, type, duration, passing_score, validity_period, 
    status, created_by
) VALUES 
(
    'GMP Fundamentals',
    'Good Manufacturing Practice fundamentals for pharmaceutical industry',
    'mandatory', 4, 80, 12, 'active', 'system'
),
(
    'Data Integrity Training', 
    'Comprehensive data integrity training for regulatory compliance',
    'compliance', 2, 85, 24, 'active', 'system'
),
(
    'Laboratory Safety',
    'Essential laboratory safety procedures and protocols', 
    'safety', 3, 75, 12, 'active', 'system'
),
(
    'Equipment Qualification',
    'Advanced equipment qualification procedures for technical staff',
    'technical', 6, 80, 18, 'active', 'system'
);

-- ============================================================================
-- SECURITY AND PERMISSIONS
-- ============================================================================

-- Create roles for different access levels
-- CREATE ROLE training_admin;
-- CREATE ROLE training_manager; 
-- CREATE ROLE training_user;

-- Grant permissions (uncomment when implementing RBAC)
-- GRANT ALL ON training_programs TO training_admin;
-- GRANT SELECT, INSERT, UPDATE ON training_programs TO training_manager;
-- GRANT SELECT ON training_programs TO training_user;

-- GRANT ALL ON training_assignments TO training_admin;
-- GRANT ALL ON training_assignments TO training_manager;
-- GRANT SELECT, UPDATE ON training_assignments TO training_user;

-- ============================================================================
-- MAINTENANCE AND CLEANUP
-- ============================================================================

-- Function to archive old completed assignments
CREATE OR REPLACE FUNCTION archive_old_assignments()
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Archive assignments completed more than 2 years ago
    WITH archived AS (
        UPDATE training_assignments 
        SET status = 'archived'
        WHERE status = 'completed' 
        AND completed_at < NOW() - INTERVAL '2 years'
        RETURNING id
    )
    SELECT COUNT(*) INTO archived_count FROM archived;
    
    RETURN archived_count;
END;
$$ language 'plpgsql';

-- ============================================================================
-- SCHEMA VALIDATION QUERIES
-- ============================================================================

-- Query to validate schema creation
SELECT 
    'training_programs' as table_name,
    COUNT(*) as record_count
FROM training_programs
UNION ALL
SELECT 
    'training_assignments' as table_name,
    COUNT(*) as record_count  
FROM training_assignments
UNION ALL
SELECT
    'training_documents' as table_name,
    COUNT(*) as record_count
FROM training_documents;

-- Query to test dashboard view
SELECT * FROM training_dashboard_stats;

-- Query to test program statistics
SELECT * FROM program_statistics LIMIT 5;

-- ============================================================================
-- MIGRATION NOTES
-- ============================================================================

/*
MIGRATION CHECKLIST:
☐ 1. Create database and user accounts
☐ 2. Run this schema file to create tables and views
☐ 3. Verify all tables created successfully
☐ 4. Test sample data insertion
☐ 5. Validate indexes and triggers
☐ 6. Set up backup procedures
☐ 7. Configure monitoring
☐ 8. Test API integration

PRODUCTION CONSIDERATIONS:
- Adjust connection limits and performance settings
- Set up proper backup schedules
- Configure monitoring and alerting
- Implement log rotation for audit tables
- Consider partitioning for large assignment tables
- Set up replication if high availability required

API INTEGRATION POINTS:
- training_programs: CRUD operations for program management
- training_assignments: Assignment creation and progress tracking  
- training_documents: EDMS document linking
- training_dashboard_stats: Real-time dashboard data
- program_statistics: Program-level analytics
*/