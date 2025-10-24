-- Training Management System (TRM) Database Schema
-- Phase 4 Implementation - QMS Platform v3.0

-- Create training-related enums
CREATE TYPE training_type AS ENUM (
    'onboarding', 'compliance', 'technical', 'safety', 'leadership', 'continuing_education'
);

CREATE TYPE training_status AS ENUM (
    'not_started', 'in_progress', 'completed', 'expired', 'overdue'
);

CREATE TYPE delivery_method AS ENUM (
    'online', 'classroom', 'hands_on', 'self_paced', 'blended'
);

CREATE TYPE competency_level AS ENUM (
    'novice', 'basic', 'intermediate', 'advanced', 'expert'
);

-- Training Programs table
CREATE TABLE training_programs (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    training_type training_type NOT NULL,
    delivery_method delivery_method NOT NULL,
    duration_hours DECIMAL(5,2),
    validity_months INTEGER,
    learning_objectives JSONB,
    prerequisites JSONB,
    materials_required JSONB,
    regulatory_requirement BOOLEAN DEFAULT FALSE,
    approval_required BOOLEAN DEFAULT TRUE,
    version VARCHAR(20) DEFAULT '1.0',
    effective_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    retirement_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Training Sessions table
CREATE TABLE training_sessions (
    id SERIAL PRIMARY KEY,
    program_id INTEGER NOT NULL REFERENCES training_programs(id),
    session_code VARCHAR(50) UNIQUE NOT NULL,
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    end_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(200),
    max_participants INTEGER,
    min_participants INTEGER,
    instructor_id INTEGER REFERENCES users(id),
    instructor_notes TEXT,
    status VARCHAR(20) DEFAULT 'scheduled',
    completion_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    CONSTRAINT valid_session_time CHECK (end_datetime > start_datetime)
);

-- Employee Training Records table
CREATE TABLE employee_training (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES users(id),
    program_id INTEGER NOT NULL REFERENCES training_programs(id),
    assigned_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    due_date TIMESTAMP WITH TIME ZONE,
    assigned_by_id INTEGER REFERENCES users(id),
    reason VARCHAR(500),
    status training_status DEFAULT 'not_started',
    start_date TIMESTAMP WITH TIME ZONE,
    completion_date TIMESTAMP WITH TIME ZONE,
    score DECIMAL(5,2),
    pass_fail BOOLEAN,
    certificate_issued BOOLEAN DEFAULT FALSE,
    certificate_number VARCHAR(100),
    certification_date TIMESTAMP WITH TIME ZONE,
    expiry_date TIMESTAMP WITH TIME ZONE,
    employee_feedback TEXT,
    supervisor_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    UNIQUE(employee_id, program_id, assigned_date)
);

-- Session Attendance table
CREATE TABLE session_attendance (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES training_sessions(id),
    employee_id INTEGER NOT NULL REFERENCES users(id),
    employee_training_id INTEGER REFERENCES employee_training(id),
    registered_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    attended BOOLEAN,
    check_in_time TIMESTAMP WITH TIME ZONE,
    check_out_time TIMESTAMP WITH TIME ZONE,
    attendance_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, employee_id)
);

-- Competencies table
CREATE TABLE competencies (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Role Competencies (required competencies per role)
CREATE TABLE role_competencies (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    competency_id INTEGER NOT NULL REFERENCES competencies(id),
    required_level competency_level NOT NULL,
    critical BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(role_id, competency_id)
);

-- Competency Mapping (training programs to competencies)
CREATE TABLE competency_mappings (
    id SERIAL PRIMARY KEY,
    program_id INTEGER NOT NULL REFERENCES training_programs(id),
    competency_id INTEGER NOT NULL REFERENCES competencies(id),
    competency_level competency_level NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(program_id, competency_id)
);

-- Competency Assessments table
CREATE TABLE competency_assessments (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES users(id),
    competency_id INTEGER NOT NULL REFERENCES competencies(id),
    assessor_id INTEGER NOT NULL REFERENCES users(id),
    assessment_date DATE NOT NULL,
    current_level competency_level NOT NULL,
    target_level competency_level,
    assessment_method VARCHAR(100),
    strengths TEXT,
    improvement_areas TEXT,
    recommended_training JSONB,
    next_assessment_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Training Assessments table
CREATE TABLE training_assessments (
    id SERIAL PRIMARY KEY,
    employee_training_id INTEGER NOT NULL REFERENCES employee_training(id),
    assessment_type VARCHAR(50),
    assessment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    max_score DECIMAL(5,2),
    achieved_score DECIMAL(5,2),
    pass_threshold DECIMAL(5,2),
    passed BOOLEAN,
    questions JSONB,
    feedback TEXT,
    improvement_recommendations TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_training_programs_code ON training_programs(code);
CREATE INDEX idx_training_programs_type ON training_programs(training_type);
CREATE INDEX idx_training_programs_active ON training_programs(retirement_date) WHERE retirement_date IS NULL;

CREATE INDEX idx_training_sessions_program ON training_sessions(program_id);
CREATE INDEX idx_training_sessions_datetime ON training_sessions(start_datetime, end_datetime);
CREATE INDEX idx_training_sessions_instructor ON training_sessions(instructor_id);

CREATE INDEX idx_employee_training_employee ON employee_training(employee_id);
CREATE INDEX idx_employee_training_program ON employee_training(program_id);
CREATE INDEX idx_employee_training_status ON employee_training(status);
CREATE INDEX idx_employee_training_due_date ON employee_training(due_date);
CREATE INDEX idx_employee_training_expiry ON employee_training(expiry_date);

CREATE INDEX idx_session_attendance_session ON session_attendance(session_id);
CREATE INDEX idx_session_attendance_employee ON session_attendance(employee_id);

CREATE INDEX idx_competencies_code ON competencies(code);
CREATE INDEX idx_competencies_category ON competencies(category);

CREATE INDEX idx_competency_assessments_employee ON competency_assessments(employee_id);
CREATE INDEX idx_competency_assessments_competency ON competency_assessments(competency_id);
CREATE INDEX idx_competency_assessments_date ON competency_assessments(assessment_date);

-- Create audit triggers for training tables
SELECT create_audit_trigger('training_programs');
SELECT create_audit_trigger('training_sessions');
SELECT create_audit_trigger('employee_training');
SELECT create_audit_trigger('session_attendance');
SELECT create_audit_trigger('competencies');
SELECT create_audit_trigger('role_competencies');
SELECT create_audit_trigger('competency_mappings');
SELECT create_audit_trigger('competency_assessments');
SELECT create_audit_trigger('training_assessments');

-- Create updated_at triggers
SELECT create_updated_at_trigger('training_programs');
SELECT create_updated_at_trigger('training_sessions');
SELECT create_updated_at_trigger('employee_training');
SELECT create_updated_at_trigger('session_attendance');
SELECT create_updated_at_trigger('competencies');
SELECT create_updated_at_trigger('role_competencies');
SELECT create_updated_at_trigger('competency_mappings');
SELECT create_updated_at_trigger('competency_assessments');
SELECT create_updated_at_trigger('training_assessments');