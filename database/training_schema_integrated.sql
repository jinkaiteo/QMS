-- ============================================================================
-- Training Management System (TMS) Integration Schema
-- For Existing QMS Platform Database - Integrated Version
-- ============================================================================

-- This schema integrates with existing QMS tables:
-- - users (existing user management)
-- - departments (existing organizational structure)  
-- - audit_logs (existing audit system)
-- - system_settings (existing configuration)

-- ============================================================================
-- ENUMS AND TYPES (Training-specific)
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
-- TRAINING CORE TABLES (Integrated with existing QMS)
-- ============================================================================

-- Training Programs Table
CREATE TABLE training_programs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    type training_type NOT NULL,
    duration INTEGER NOT NULL CHECK (duration > 0), -- in hours
    passing_score INTEGER DEFAULT 70 CHECK (passing_score BETWEEN 0 AND 100),
    validity_period INTEGER DEFAULT 12 CHECK (validity_period > 0), -- in months
    status program_status DEFAULT 'draft',
    
    -- Integration with existing QMS tables
    created_by INTEGER REFERENCES users(id), -- Use existing users table
    updated_by INTEGER REFERENCES users(id),
    department_id INTEGER REFERENCES departments(id), -- Use existing departments
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    retired_at TIMESTAMP WITH TIME ZONE,
    retirement_reason TEXT,
    
    -- Version control
    version INTEGER DEFAULT 1,
    supersedes_id INTEGER REFERENCES training_programs(id),
    
    -- Constraints
    CONSTRAINT valid_title CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT valid_duration CHECK (duration BETWEEN 1 AND 168) -- max 1 week
);

-- Training Program Modules (for future phase 2)
CREATE TABLE training_modules (
    id SERIAL PRIMARY KEY,
    program_id INTEGER NOT NULL REFERENCES training_programs(id) ON DELETE CASCADE,
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

-- Training Assignments Table (Integrated with existing users)
CREATE TABLE training_assignments (
    id SERIAL PRIMARY KEY,
    program_id INTEGER NOT NULL REFERENCES training_programs(id),
    employee_id INTEGER NOT NULL REFERENCES users(id), -- Use existing users table
    
    -- Assignment details
    assigned_by INTEGER NOT NULL REFERENCES users(id), -- Use existing users table
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
    
    -- Audit trail (will integrate with existing audit_logs via triggers)
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
    ),
    
    -- Unique constraint to prevent duplicate assignments
    UNIQUE(program_id, employee_id)
);

-- Training Documents (EDMS Integration)
CREATE TABLE training_documents (
    id SERIAL PRIMARY KEY,
    program_id INTEGER NOT NULL REFERENCES training_programs(id) ON DELETE CASCADE,
    
    -- Document references (integrate with existing document system if available)
    document_id VARCHAR(100) NOT NULL, -- EDMS document ID
    document_title VARCHAR(255) NOT NULL,
    document_type document_type NOT NULL,
    category document_category NOT NULL,
    document_version VARCHAR(20),
    
    -- Relationship
    is_required BOOLEAN DEFAULT false,
    sequence_order INTEGER DEFAULT 0,
    
    -- Metadata (integrated with existing users)
    linked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    linked_by INTEGER NOT NULL REFERENCES users(id),
    
    UNIQUE(program_id, document_id),
    CONSTRAINT valid_document_title CHECK (LENGTH(TRIM(document_title)) > 0)
);

-- Training Prerequisites (for future phase 2)
CREATE TABLE training_prerequisites (
    id SERIAL PRIMARY KEY,
    program_id INTEGER NOT NULL REFERENCES training_programs(id) ON DELETE CASCADE,
    prerequisite_program_id INTEGER NOT NULL REFERENCES training_programs(id),
    is_required BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(program_id, prerequisite_program_id),
    CONSTRAINT no_self_prerequisite CHECK (program_id != prerequisite_program_id)
);

-- ============================================================================
-- INTEGRATION WITH EXISTING AUDIT SYSTEM
-- ============================================================================

-- Function to log training changes to existing audit_logs table
CREATE OR REPLACE FUNCTION log_training_audit(
    p_table_name VARCHAR,
    p_record_id INTEGER,
    p_action VARCHAR,
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL,
    p_user_id INTEGER DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    -- Insert into existing audit_logs table
    INSERT INTO audit_logs (
        table_name,
        record_id,
        action,
        old_values,
        new_values,
        user_id,
        timestamp,
        ip_address
    ) VALUES (
        p_table_name,
        p_record_id,
        p_action,
        p_old_values,
        p_new_values,
        p_user_id,
        NOW(),
        inet_client_addr()
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR INTEGRATION WITH EXISTING AUDIT SYSTEM
-- ============================================================================

-- Trigger function for training programs audit
CREATE OR REPLACE FUNCTION audit_training_programs() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM log_training_audit(
            'training_programs',
            OLD.id,
            'DELETE',
            row_to_json(OLD)::jsonb,
            NULL,
            OLD.updated_by
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM log_training_audit(
            'training_programs',
            NEW.id,
            'UPDATE',
            row_to_json(OLD)::jsonb,
            row_to_json(NEW)::jsonb,
            NEW.updated_by
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        PERFORM log_training_audit(
            'training_programs',
            NEW.id,
            'INSERT',
            NULL,
            row_to_json(NEW)::jsonb,
            NEW.created_by
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger function for training assignments audit
CREATE OR REPLACE FUNCTION audit_training_assignments() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM log_training_audit(
            'training_assignments',
            OLD.id,
            'DELETE',
            row_to_json(OLD)::jsonb,
            NULL,
            NULL
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM log_training_audit(
            'training_assignments',
            NEW.id,
            'UPDATE',
            row_to_json(OLD)::jsonb,
            row_to_json(NEW)::jsonb,
            NEW.assigned_by
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        PERFORM log_training_audit(
            'training_assignments',
            NEW.id,
            'INSERT',
            NULL,
            row_to_json(NEW)::jsonb,
            NEW.assigned_by
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers
CREATE TRIGGER training_programs_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON training_programs
    FOR EACH ROW EXECUTE FUNCTION audit_training_programs();

CREATE TRIGGER training_assignments_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON training_assignments
    FOR EACH ROW EXECUTE FUNCTION audit_training_assignments();

-- ============================================================================
-- INTEGRATION VIEWS FOR DASHBOARD AND ANALYTICS
-- ============================================================================

-- Training Dashboard Statistics View (Integrated)
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

-- Program Statistics View (Integrated with users and departments)
CREATE VIEW program_statistics AS
SELECT 
    tp.id,
    tp.title,
    tp.type,
    tp.status,
    tp.department_id,
    d.name as department_name,
    u.username as created_by_username,
    COUNT(ta.id) as total_assignments,
    COUNT(CASE WHEN ta.status = 'completed' THEN 1 END) as completed_assignments,
    COUNT(CASE WHEN ta.status IN ('assigned', 'not_started', 'in_progress') THEN 1 END) as active_assignments,
    COUNT(CASE WHEN ta.status IN ('assigned', 'not_started', 'in_progress') AND ta.due_date < NOW() THEN 1 END) as overdue_assignments,
    ROUND(AVG(CASE WHEN ta.status = 'completed' THEN ta.score END), 1) as average_score,
    tp.created_at,
    tp.updated_at
FROM training_programs tp
LEFT JOIN training_assignments ta ON tp.id = ta.program_id
LEFT JOIN departments d ON tp.department_id = d.id
LEFT JOIN users u ON tp.created_by = u.id
GROUP BY tp.id, tp.title, tp.type, tp.status, tp.department_id, d.name, u.username, tp.created_at, tp.updated_at;

-- Employee Training Summary (New useful view)
CREATE VIEW employee_training_summary AS
SELECT 
    u.id as employee_id,
    u.username,
    u.first_name,
    u.last_name,
    u.email,
    d.name as department_name,
    COUNT(ta.id) as total_assignments,
    COUNT(CASE WHEN ta.status = 'completed' THEN 1 END) as completed_trainings,
    COUNT(CASE WHEN ta.status IN ('assigned', 'not_started', 'in_progress') THEN 1 END) as pending_trainings,
    COUNT(CASE WHEN ta.status IN ('assigned', 'not_started', 'in_progress') AND ta.due_date < NOW() THEN 1 END) as overdue_trainings,
    ROUND(AVG(CASE WHEN ta.status = 'completed' THEN ta.score END), 1) as average_score,
    MAX(ta.completed_at) as last_training_completed
FROM users u
LEFT JOIN departments d ON u.department_id = d.id
LEFT JOIN training_assignments ta ON u.id = ta.employee_id
GROUP BY u.id, u.username, u.first_name, u.last_name, u.email, d.name;

-- ============================================================================
-- INDEXES FOR PERFORMANCE (Integrated)
-- ============================================================================

-- Training Programs Indexes
CREATE INDEX idx_training_programs_status ON training_programs(status);
CREATE INDEX idx_training_programs_type ON training_programs(type);
CREATE INDEX idx_training_programs_created_by ON training_programs(created_by);
CREATE INDEX idx_training_programs_department ON training_programs(department_id);
CREATE INDEX idx_training_programs_created_at ON training_programs(created_at);

-- Training Assignments Indexes
CREATE INDEX idx_training_assignments_program_id ON training_assignments(program_id);
CREATE INDEX idx_training_assignments_employee_id ON training_assignments(employee_id);
CREATE INDEX idx_training_assignments_assigned_by ON training_assignments(assigned_by);
CREATE INDEX idx_training_assignments_status ON training_assignments(status);
CREATE INDEX idx_training_assignments_due_date ON training_assignments(due_date);
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
CREATE INDEX idx_training_documents_linked_by ON training_documents(linked_by);

-- ============================================================================
-- UPDATE TRIGGER FOR TIMESTAMP MANAGEMENT
-- ============================================================================

-- Update timestamp trigger function (reuse existing if available)
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

-- ============================================================================
-- SAMPLE DATA (Integrated with existing users and departments)
-- ============================================================================

-- Insert sample training programs (will use actual user IDs and department IDs)
DO $$
DECLARE
    sample_user_id INTEGER;
    sample_dept_id INTEGER;
BEGIN
    -- Get first active user for sample data
    SELECT id INTO sample_user_id FROM users WHERE is_active = true LIMIT 1;
    
    -- Get first department for sample data  
    SELECT id INTO sample_dept_id FROM departments LIMIT 1;
    
    -- Only insert sample data if we have users and departments
    IF sample_user_id IS NOT NULL AND sample_dept_id IS NOT NULL THEN
        INSERT INTO training_programs (
            title, description, type, duration, passing_score, validity_period, 
            status, created_by, department_id
        ) VALUES 
        (
            'GMP Fundamentals',
            'Good Manufacturing Practice fundamentals for pharmaceutical industry',
            'mandatory', 4, 80, 12, 'active', sample_user_id, sample_dept_id
        ),
        (
            'Data Integrity Training', 
            'Comprehensive data integrity training for regulatory compliance',
            'compliance', 2, 85, 24, 'active', sample_user_id, sample_dept_id
        ),
        (
            'Laboratory Safety',
            'Essential laboratory safety procedures and protocols', 
            'safety', 3, 75, 12, 'active', sample_user_id, sample_dept_id
        ),
        (
            'Equipment Qualification',
            'Advanced equipment qualification procedures for technical staff',
            'technical', 6, 80, 18, 'active', sample_user_id, sample_dept_id
        );
    END IF;
END $$;

-- ============================================================================
-- SYSTEM SETTINGS INTEGRATION
-- ============================================================================

-- Add training-related system settings to existing system_settings table
INSERT INTO system_settings (key, value, description, created_at) VALUES
('training.default_passing_score', '70', 'Default passing score percentage for training programs', NOW()),
('training.default_validity_period', '12', 'Default validity period in months for training programs', NOW()),
('training.max_attempts', '3', 'Maximum number of attempts allowed for training assessments', NOW()),
('training.reminder_days', '7,3,1', 'Days before due date to send reminder notifications', NOW()),
('training.auto_archive_days', '730', 'Days after completion to auto-archive training records', NOW())
ON CONFLICT (key) DO NOTHING; -- Don't overwrite if settings already exist

-- ============================================================================
-- INTEGRATION VALIDATION QUERIES
-- ============================================================================

-- Query to validate integration with existing tables
SELECT 
    'Integration Check' as check_type,
    'Users Integration' as check_name,
    CASE WHEN EXISTS (SELECT 1 FROM users LIMIT 1) THEN 'PASS' ELSE 'FAIL' END as status,
    (SELECT COUNT(*) FROM users) as user_count;

SELECT 
    'Integration Check' as check_type,
    'Departments Integration' as check_name,
    CASE WHEN EXISTS (SELECT 1 FROM departments LIMIT 1) THEN 'PASS' ELSE 'FAIL' END as status,
    (SELECT COUNT(*) FROM departments) as department_count;

SELECT 
    'Integration Check' as check_type,
    'Audit Logs Integration' as check_name,
    CASE WHEN EXISTS (SELECT 1 FROM audit_logs LIMIT 1) THEN 'PASS' ELSE 'FAIL' END as status,
    (SELECT COUNT(*) FROM audit_logs) as audit_count;

-- Final validation
SELECT 
    'Training Schema' as validation_type,
    COUNT(*) as training_tables_created
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'training_%';

-- Test dashboard view
SELECT 'Dashboard Test' as test_type, * FROM training_dashboard_stats;

-- Test integration views
SELECT 'Program Statistics Test' as test_type, COUNT(*) as programs FROM program_statistics;
SELECT 'Employee Summary Test' as test_type, COUNT(*) as employees FROM employee_training_summary;

-- ============================================================================
-- INTEGRATION NOTES AND NEXT STEPS
-- ============================================================================

/*
INTEGRATION COMPLETED:
✅ Training tables created with references to existing users, departments
✅ Audit integration with existing audit_logs table
✅ System settings integration for training configuration
✅ Views created that join with existing organizational structure
✅ Sample data inserted using real user and department IDs
✅ Indexes optimized for integrated queries
✅ Triggers configured for audit trail integration

NEXT STEPS:
1. Verify integration by querying views
2. Test training program creation with real users
3. Add training endpoints to existing backend API
4. Update frontend to use existing backend (port 8000)
5. Test complete integration workflow

API INTEGRATION POINTS:
- Use existing user authentication system
- Leverage existing department structure
- Integrate with existing audit logging
- Extend existing API with training endpoints
- Use existing system configuration framework
*/