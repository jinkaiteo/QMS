-- QRM Tables Creation - Phase 3
-- Quality Risk Management tables

-- Quality event types and classifications
CREATE TABLE quality_event_types (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    severity_levels TEXT[], -- Array of allowed severity levels
    color VARCHAR(7), -- Hex color code for UI
    icon VARCHAR(50), -- Icon identifier
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Quality events (incidents, deviations, complaints, etc.)
CREATE TABLE quality_events (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    event_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    event_type_id INTEGER REFERENCES quality_event_types(id) NOT NULL,
    severity VARCHAR(50) NOT NULL, -- critical, major, minor, informational
    priority INTEGER DEFAULT 3, -- 1=High, 2=Medium, 3=Low
    source VARCHAR(100), -- customer_complaint, internal_audit, inspection, etc.
    
    -- Event details
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    location VARCHAR(255),
    department_id INTEGER REFERENCES departments(id),
    
    -- People involved
    reporter_id INTEGER REFERENCES users(id) NOT NULL,
    assigned_to INTEGER REFERENCES users(id),
    investigator_id INTEGER REFERENCES users(id),
    
    -- Product/Process impact
    product_affected VARCHAR(255),
    batch_lot_numbers TEXT[],
    processes_affected TEXT[],
    
    -- Impact assessment
    patient_safety_impact BOOLEAN DEFAULT FALSE,
    product_quality_impact BOOLEAN DEFAULT FALSE,
    regulatory_impact BOOLEAN DEFAULT FALSE,
    business_impact_severity VARCHAR(50), -- low, medium, high, critical
    estimated_cost DECIMAL(12,2),
    
    -- Status and workflow
    status quality_event_status DEFAULT 'open',
    investigation_required BOOLEAN DEFAULT TRUE,
    capa_required BOOLEAN DEFAULT FALSE,
    regulatory_reporting_required BOOLEAN DEFAULT FALSE,
    
    -- Dates and deadlines
    investigation_due_date DATE,
    capa_due_date DATE,
    regulatory_due_date DATE,
    target_closure_date DATE,
    actual_closure_date DATE,
    
    -- Resolution
    root_cause TEXT,
    immediate_actions TEXT,
    containment_actions TEXT,
    
    -- Compliance
    gmp_classification VARCHAR(50), -- critical, major, minor, observation
    regulatory_citations TEXT[],
    
    -- Relationships
    parent_event_id INTEGER REFERENCES quality_events(id),
    related_documents INTEGER[], -- Array of document IDs
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Quality event investigations
CREATE TABLE quality_investigations (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    quality_event_id INTEGER REFERENCES quality_events(id) NOT NULL,
    investigation_number VARCHAR(100) UNIQUE NOT NULL,
    
    -- Investigation team
    lead_investigator_id INTEGER REFERENCES users(id) NOT NULL,
    team_members INTEGER[], -- Array of user IDs
    
    -- Investigation details
    methodology VARCHAR(100), -- 5_why, fishbone, fault_tree, etc.
    scope_definition TEXT,
    timeline_of_events TEXT,
    evidence_collected TEXT,
    interviews_conducted TEXT,
    
    -- Root cause analysis
    immediate_cause TEXT,
    root_cause TEXT,
    contributing_factors TEXT,
    
    -- Risk assessment
    risk_level VARCHAR(50), -- low, medium, high, critical
    risk_score INTEGER, -- 1-25 scale
    likelihood VARCHAR(50), -- rare, unlikely, possible, likely, certain
    severity_impact VARCHAR(50), -- negligible, minor, moderate, major, catastrophic
    
    -- Investigation status
    status investigation_status DEFAULT 'planning',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Documentation
    investigation_report_path VARCHAR(500),
    evidence_documents INTEGER[], -- Array of document IDs
    
    -- Approval
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- CAPA (Corrective and Preventive Actions)
CREATE TABLE capas (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    capa_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    
    -- CAPA classification
    capa_type capa_type NOT NULL, -- corrective, preventive, improvement
    action_category VARCHAR(100), -- process_change, training, procedure_update, etc.
    
    -- Source and relationships
    source_type VARCHAR(100), -- quality_event, audit_finding, management_review
    source_id INTEGER, -- ID of the source record
    quality_event_id INTEGER REFERENCES quality_events(id),
    investigation_id INTEGER REFERENCES quality_investigations(id),
    
    -- Assignment and responsibility
    owner_id INTEGER REFERENCES users(id) NOT NULL,
    responsible_department_id INTEGER REFERENCES departments(id),
    assigned_to INTEGER REFERENCES users(id),
    
    -- CAPA details
    problem_statement TEXT NOT NULL,
    root_cause TEXT,
    proposed_solution TEXT NOT NULL,
    implementation_plan TEXT,
    success_criteria TEXT,
    
    -- Timeline
    target_start_date DATE,
    target_completion_date DATE NOT NULL,
    actual_start_date DATE,
    actual_completion_date DATE,
    
    -- Resources
    estimated_cost DECIMAL(12,2),
    actual_cost DECIMAL(12,2),
    resources_required TEXT,
    
    -- Priority and risk
    priority INTEGER DEFAULT 3, -- 1=High, 2=Medium, 3=Low
    risk_level VARCHAR(50), -- low, medium, high, critical
    
    -- Status tracking
    status capa_status DEFAULT 'planning',
    completion_percentage INTEGER DEFAULT 0,
    
    -- Effectiveness verification
    verification_method TEXT,
    verification_criteria TEXT,
    verification_due_date DATE,
    verification_completed_date DATE,
    effectiveness_confirmed BOOLEAN DEFAULT FALSE,
    verification_comments TEXT,
    
    -- Approval workflow
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Related documents and training
    related_documents INTEGER[], -- Array of document IDs
    training_required BOOLEAN DEFAULT FALSE,
    training_plan_id INTEGER, -- Reference to training records
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- CAPA actions/tasks (breakdown of CAPAs into actionable items)
CREATE TABLE capa_actions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    capa_id INTEGER REFERENCES capas(id) NOT NULL,
    action_number VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Assignment
    assigned_to INTEGER REFERENCES users(id) NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    
    -- Timeline
    due_date DATE NOT NULL,
    completed_date DATE,
    
    -- Status
    status action_status DEFAULT 'open',
    completion_percentage INTEGER DEFAULT 0,
    
    -- Dependencies
    depends_on INTEGER[], -- Array of other action IDs
    
    -- Evidence and verification
    completion_evidence TEXT,
    verification_required BOOLEAN DEFAULT FALSE,
    verified_by INTEGER REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    
    UNIQUE(capa_id, action_number)
);

-- Change control requests
CREATE TABLE change_control_requests (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    change_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    
    -- Change classification
    change_type change_type NOT NULL, -- major, minor, emergency
    change_category VARCHAR(100), -- process, equipment, facility, system, document
    urgency VARCHAR(50), -- routine, urgent, emergency
    
    -- Initiator and assignment
    initiator_id INTEGER REFERENCES users(id) NOT NULL,
    assigned_to INTEGER REFERENCES users(id),
    change_owner_id INTEGER REFERENCES users(id),
    affected_departments INTEGER[], -- Array of department IDs
    
    -- Change details
    current_state TEXT NOT NULL,
    proposed_state TEXT NOT NULL,
    justification TEXT NOT NULL,
    benefits TEXT,
    
    -- Impact assessment
    validation_impact BOOLEAN DEFAULT FALSE,
    gmp_impact BOOLEAN DEFAULT FALSE,
    regulatory_impact BOOLEAN DEFAULT FALSE,
    safety_impact BOOLEAN DEFAULT FALSE,
    environmental_impact BOOLEAN DEFAULT FALSE,
    
    -- Risk assessment
    risk_assessment TEXT,
    risk_level VARCHAR(50), -- low, medium, high, critical
    mitigation_measures TEXT,
    
    -- Implementation
    implementation_plan TEXT,
    rollback_plan TEXT,
    testing_requirements TEXT,
    training_requirements TEXT,
    documentation_updates TEXT,
    
    -- Timeline
    requested_date DATE NOT NULL,
    target_implementation_date DATE,
    actual_implementation_date DATE,
    
    -- Resources
    estimated_cost DECIMAL(12,2),
    actual_cost DECIMAL(12,2),
    resources_required TEXT,
    
    -- Status and approval
    status change_status DEFAULT 'submitted',
    priority INTEGER DEFAULT 3,
    
    -- Approval workflow
    technical_reviewer_id INTEGER REFERENCES users(id),
    technical_review_date DATE,
    technical_review_comments TEXT,
    
    quality_reviewer_id INTEGER REFERENCES users(id),
    quality_review_date DATE,
    quality_review_comments TEXT,
    
    final_approver_id INTEGER REFERENCES users(id),
    final_approval_date DATE,
    final_approval_comments TEXT,
    
    -- Implementation tracking
    implementation_verified BOOLEAN DEFAULT FALSE,
    verified_by INTEGER REFERENCES users(id),
    verification_date DATE,
    verification_comments TEXT,
    
    -- Post-implementation
    effectiveness_review_due_date DATE,
    effectiveness_confirmed BOOLEAN DEFAULT FALSE,
    effectiveness_comments TEXT,
    
    -- Related records
    related_quality_events INTEGER[], -- Array of quality event IDs
    related_capas INTEGER[], -- Array of CAPA IDs
    related_documents INTEGER[], -- Array of document IDs
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Risk assessments
CREATE TABLE risk_assessments (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    assessment_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    
    -- Assessment type and scope
    assessment_type VARCHAR(100), -- process, product, facility, system
    methodology VARCHAR(100), -- fmea, hazop, bow_tie, preliminary_hazard
    scope_definition TEXT NOT NULL,
    
    -- Assessment team
    lead_assessor_id INTEGER REFERENCES users(id) NOT NULL,
    team_members INTEGER[], -- Array of user IDs
    
    -- Risk criteria
    risk_matrix JSONB, -- Risk matrix configuration
    likelihood_scale JSONB, -- Likelihood scale definition
    severity_scale JSONB, -- Severity scale definition
    
    -- Assessment results
    identified_risks JSONB, -- Array of identified risks
    risk_scores JSONB, -- Risk scoring results
    control_measures JSONB, -- Existing control measures
    residual_risks JSONB, -- Risks after controls
    
    -- Overall assessment
    overall_risk_level VARCHAR(50), -- low, medium, high, critical
    acceptability VARCHAR(50), -- acceptable, tolerable, unacceptable
    
    -- Action items
    recommended_actions TEXT,
    action_plan TEXT,
    
    -- Status and approval
    status assessment_status DEFAULT 'planning',
    completed_date DATE,
    
    -- Review and approval
    reviewed_by INTEGER REFERENCES users(id),
    review_date DATE,
    review_comments TEXT,
    
    approved_by INTEGER REFERENCES users(id),
    approval_date DATE,
    approval_comments TEXT,
    
    -- Periodic review
    review_frequency_months INTEGER DEFAULT 12,
    next_review_due_date DATE,
    
    -- Related records
    related_processes TEXT[],
    related_products TEXT[],
    related_documents INTEGER[], -- Array of document IDs
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Create additional enums for QRM
CREATE TYPE quality_event_status AS ENUM (
    'open', 'investigating', 'capa_pending', 'capa_in_progress', 
    'under_review', 'closed', 'cancelled'
);

CREATE TYPE investigation_status AS ENUM (
    'planning', 'in_progress', 'evidence_review', 'analysis', 
    'report_writing', 'under_review', 'approved', 'closed'
);

CREATE TYPE capa_type AS ENUM ('corrective', 'preventive', 'improvement');

CREATE TYPE capa_status AS ENUM (
    'planning', 'approved', 'in_progress', 'implemented', 
    'verification_pending', 'verified', 'closed', 'cancelled'
);

CREATE TYPE action_status AS ENUM ('open', 'in_progress', 'completed', 'verified', 'cancelled');

CREATE TYPE change_type AS ENUM ('major', 'minor', 'emergency');

CREATE TYPE change_status AS ENUM (
    'submitted', 'under_review', 'approved', 'rejected', 
    'implementation_pending', 'implementing', 'implemented', 
    'verification_pending', 'verified', 'closed', 'cancelled'
);

CREATE TYPE assessment_status AS ENUM (
    'planning', 'in_progress', 'under_review', 'approved', 
    'implementation_pending', 'active', 'expired', 'superseded'
);

-- Create indexes for performance
CREATE INDEX idx_quality_events_number ON quality_events(event_number);
CREATE INDEX idx_quality_events_type ON quality_events(event_type_id);
CREATE INDEX idx_quality_events_severity ON quality_events(severity);
CREATE INDEX idx_quality_events_status ON quality_events(status);
CREATE INDEX idx_quality_events_reporter ON quality_events(reporter_id);
CREATE INDEX idx_quality_events_occurred ON quality_events(occurred_at);
CREATE INDEX idx_quality_events_department ON quality_events(department_id);

CREATE INDEX idx_quality_investigations_event ON quality_investigations(quality_event_id);
CREATE INDEX idx_quality_investigations_investigator ON quality_investigations(lead_investigator_id);
CREATE INDEX idx_quality_investigations_status ON quality_investigations(status);

CREATE INDEX idx_capas_number ON capas(capa_number);
CREATE INDEX idx_capas_type ON capas(capa_type);
CREATE INDEX idx_capas_status ON capas(status);
CREATE INDEX idx_capas_owner ON capas(owner_id);
CREATE INDEX idx_capas_quality_event ON capas(quality_event_id);
CREATE INDEX idx_capas_due_date ON capas(target_completion_date);

CREATE INDEX idx_capa_actions_capa ON capa_actions(capa_id);
CREATE INDEX idx_capa_actions_assigned ON capa_actions(assigned_to);
CREATE INDEX idx_capa_actions_status ON capa_actions(status);
CREATE INDEX idx_capa_actions_due_date ON capa_actions(due_date);

CREATE INDEX idx_change_control_number ON change_control_requests(change_number);
CREATE INDEX idx_change_control_type ON change_control_requests(change_type);
CREATE INDEX idx_change_control_status ON change_control_requests(status);
CREATE INDEX idx_change_control_initiator ON change_control_requests(initiator_id);
CREATE INDEX idx_change_control_target_date ON change_control_requests(target_implementation_date);

CREATE INDEX idx_risk_assessments_number ON risk_assessments(assessment_number);
CREATE INDEX idx_risk_assessments_type ON risk_assessments(assessment_type);
CREATE INDEX idx_risk_assessments_status ON risk_assessments(status);
CREATE INDEX idx_risk_assessments_assessor ON risk_assessments(lead_assessor_id);
CREATE INDEX idx_risk_assessments_due_date ON risk_assessments(next_review_due_date);

-- Add triggers for automatic timestamp updates
CREATE TRIGGER update_quality_event_types_updated_at 
    BEFORE UPDATE ON quality_event_types 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quality_events_updated_at 
    BEFORE UPDATE ON quality_events 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quality_investigations_updated_at 
    BEFORE UPDATE ON quality_investigations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_capas_updated_at 
    BEFORE UPDATE ON capas 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_capa_actions_updated_at 
    BEFORE UPDATE ON capa_actions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_change_control_requests_updated_at 
    BEFORE UPDATE ON change_control_requests 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_risk_assessments_updated_at 
    BEFORE UPDATE ON risk_assessments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add audit triggers for compliance
CREATE TRIGGER audit_quality_events_trigger
    AFTER INSERT OR UPDATE OR DELETE ON quality_events
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_quality_investigations_trigger
    AFTER INSERT OR UPDATE OR DELETE ON quality_investigations
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_capas_trigger
    AFTER INSERT OR UPDATE OR DELETE ON capas
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_capa_actions_trigger
    AFTER INSERT OR UPDATE OR DELETE ON capa_actions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_change_control_requests_trigger
    AFTER INSERT OR UPDATE OR DELETE ON change_control_requests
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_risk_assessments_trigger
    AFTER INSERT OR UPDATE OR DELETE ON risk_assessments
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO qms_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO qms_user;

-- Comments for documentation
COMMENT ON TABLE quality_event_types IS 'Phase 3: Types and classifications for quality events';
COMMENT ON TABLE quality_events IS 'Phase 3: Main quality events registry (deviations, complaints, etc.)';
COMMENT ON TABLE quality_investigations IS 'Phase 3: Formal investigations for quality events';
COMMENT ON TABLE capas IS 'Phase 3: Corrective and Preventive Actions management';
COMMENT ON TABLE capa_actions IS 'Phase 3: Individual action items within CAPAs';
COMMENT ON TABLE change_control_requests IS 'Phase 3: Change control and management';
COMMENT ON TABLE risk_assessments IS 'Phase 3: Risk assessment and management';

COMMENT ON COLUMN quality_events.event_number IS 'Unique identifier for quality events';
COMMENT ON COLUMN quality_events.severity IS 'Impact severity classification';
COMMENT ON COLUMN capas.capa_type IS 'Corrective, preventive, or improvement action';
COMMENT ON COLUMN change_control_requests.change_type IS 'Major, minor, or emergency change';
COMMENT ON COLUMN risk_assessments.risk_matrix IS 'JSON configuration for risk scoring matrix';