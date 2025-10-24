-- Laboratory Information Management System (LIMS) Database Schema
-- Phase 5 Implementation - QMS Platform v3.0
-- Database Migration for Production Deployment

-- Create LIMS-related enums
CREATE TYPE sample_category AS ENUM (
    'raw_material', 'finished_product', 'in_process', 'stability', 'reference_standard', 'environmental'
);

CREATE TYPE sample_status AS ENUM (
    'received', 'in_testing', 'testing_complete', 'approved', 'rejected', 'disposed'
);

CREATE TYPE test_status AS ENUM (
    'pending', 'in_progress', 'completed', 'reviewed', 'approved', 'rejected'
);

CREATE TYPE instrument_status AS ENUM (
    'qualified', 'calibration_due', 'out_of_service', 'maintenance_required'
);

-- Sample Types table
CREATE TABLE sample_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category sample_category NOT NULL,
    description TEXT,
    storage_temperature_min DECIMAL(5,2),
    storage_temperature_max DECIMAL(5,2),
    storage_humidity_max DECIMAL(5,2),
    storage_conditions TEXT,
    shelf_life_days INTEGER,
    hazard_classification VARCHAR(100),
    regulatory_category VARCHAR(100),
    disposal_instructions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Samples table
CREATE TABLE samples (
    id SERIAL PRIMARY KEY,
    sample_id VARCHAR(50) UNIQUE NOT NULL,
    sample_type_id INTEGER NOT NULL REFERENCES sample_types(id),
    batch_lot_number VARCHAR(100) NOT NULL,
    supplier_reference VARCHAR(100),
    internal_reference VARCHAR(100),
    collection_date TIMESTAMP WITH TIME ZONE NOT NULL,
    received_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expiry_date TIMESTAMP WITH TIME ZONE,
    quantity DECIMAL(10,3),
    quantity_units VARCHAR(20),
    storage_location VARCHAR(200),
    collected_by VARCHAR(200),
    received_by_id INTEGER REFERENCES users(id),
    current_custodian_id INTEGER REFERENCES users(id),
    status sample_status DEFAULT 'received',
    temperature_on_receipt DECIMAL(5,2),
    condition_on_receipt TEXT,
    chain_of_custody JSONB,
    priority_level VARCHAR(20) DEFAULT 'normal',
    special_instructions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Test Methods table
CREATE TABLE test_methods (
    id SERIAL PRIMARY KEY,
    method_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    procedure_document_id INTEGER REFERENCES documents(id),
    method_type VARCHAR(100),
    estimated_duration_hours DECIMAL(4,2),
    equipment_required JSONB,
    analyst_qualifications JSONB,
    environmental_requirements JSONB,
    validation_status VARCHAR(50) DEFAULT 'draft',
    approved_by_id INTEGER REFERENCES users(id),
    approval_date TIMESTAMP WITH TIME ZONE,
    effective_date TIMESTAMP WITH TIME ZONE,
    retirement_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Test Specifications table
CREATE TABLE test_specifications (
    id SERIAL PRIMARY KEY,
    sample_type_id INTEGER NOT NULL REFERENCES sample_types(id),
    test_method_id INTEGER NOT NULL REFERENCES test_methods(id),
    parameter_name VARCHAR(200) NOT NULL,
    specification_type VARCHAR(50),
    lower_limit DECIMAL(15,6),
    upper_limit DECIMAL(15,6),
    target_value DECIMAL(15,6),
    units VARCHAR(50),
    regulatory_requirement BOOLEAN DEFAULT FALSE,
    criticality_level VARCHAR(20) DEFAULT 'normal',
    statistical_approach VARCHAR(100),
    version VARCHAR(20) DEFAULT '1.0',
    effective_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    UNIQUE(sample_type_id, test_method_id, parameter_name)
);

-- Instruments table
CREATE TABLE instruments (
    id SERIAL PRIMARY KEY,
    instrument_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    manufacturer VARCHAR(200),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    asset_number VARCHAR(100),
    purchase_date DATE,
    warranty_expiry DATE,
    location VARCHAR(200),
    department VARCHAR(100),
    status instrument_status DEFAULT 'qualified',
    calibration_frequency_days INTEGER DEFAULT 365,
    last_calibration_date DATE,
    next_calibration_due DATE,
    maintenance_frequency_days INTEGER DEFAULT 90,
    last_maintenance_date DATE,
    next_maintenance_due DATE,
    specifications JSONB,
    operating_ranges JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Test Executions table
CREATE TABLE test_executions (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(50) UNIQUE NOT NULL,
    sample_id INTEGER NOT NULL REFERENCES samples(id),
    test_method_id INTEGER NOT NULL REFERENCES test_methods(id),
    analyst_id INTEGER NOT NULL REFERENCES users(id),
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    completion_datetime TIMESTAMP WITH TIME ZONE,
    status test_status DEFAULT 'pending',
    instrument_id INTEGER REFERENCES instruments(id),
    environmental_conditions JSONB,
    reagent_lot_numbers JSONB,
    reviewed_by_id INTEGER REFERENCES users(id),
    review_date TIMESTAMP WITH TIME ZONE,
    approved_by_id INTEGER REFERENCES users(id),
    approval_date TIMESTAMP WITH TIME ZONE,
    analyst_notes TEXT,
    deviations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Test Results table
CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    test_execution_id INTEGER NOT NULL REFERENCES test_executions(id),
    test_specification_id INTEGER NOT NULL REFERENCES test_specifications(id),
    parameter_name VARCHAR(200) NOT NULL,
    result_value DECIMAL(15,6),
    result_text TEXT,
    units VARCHAR(50),
    pass_fail BOOLEAN,
    out_of_specification BOOLEAN DEFAULT FALSE,
    deviation_percent DECIMAL(8,3),
    replicate_values JSONB,
    mean_value DECIMAL(15,6),
    standard_deviation DECIMAL(15,6),
    relative_standard_deviation DECIMAL(8,3),
    raw_data_file VARCHAR(500),
    data_hash VARCHAR(128),
    electronic_signature JSONB,
    reviewed_by_id INTEGER REFERENCES users(id),
    review_date TIMESTAMP WITH TIME ZONE,
    review_comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Calibration Records table
CREATE TABLE calibration_records (
    id SERIAL PRIMARY KEY,
    calibration_id VARCHAR(50) UNIQUE NOT NULL,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id),
    calibration_date DATE NOT NULL,
    next_due_date DATE NOT NULL,
    calibration_type VARCHAR(100),
    calibration_standard VARCHAR(200),
    standard_certificate VARCHAR(200),
    standard_expiry_date DATE,
    reference_values JSONB,
    calibration_results JSONB,
    accuracy_check BOOLEAN,
    precision_check BOOLEAN,
    linearity_check BOOLEAN,
    overall_result VARCHAR(20),
    performed_by_id INTEGER NOT NULL REFERENCES users(id),
    witnessed_by_id INTEGER REFERENCES users(id),
    approved_by_id INTEGER REFERENCES users(id),
    approval_date TIMESTAMP WITH TIME ZONE,
    certificate_reference VARCHAR(200),
    calibration_report_path VARCHAR(500),
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- LIMS Audit Log table (specialized for LIMS data integrity)
CREATE TABLE lims_audit_log (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL,
    entity_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    change_reason TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(128),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance optimization
CREATE INDEX idx_sample_types_code ON sample_types(code);
CREATE INDEX idx_sample_types_category ON sample_types(category);

CREATE INDEX idx_samples_sample_id ON samples(sample_id);
CREATE INDEX idx_samples_batch_lot ON samples(batch_lot_number);
CREATE INDEX idx_samples_status ON samples(status);
CREATE INDEX idx_samples_type ON samples(sample_type_id);
CREATE INDEX idx_samples_received_date ON samples(received_date);
CREATE INDEX idx_samples_custodian ON samples(current_custodian_id);

CREATE INDEX idx_test_methods_code ON test_methods(method_code);
CREATE INDEX idx_test_methods_status ON test_methods(validation_status);
CREATE INDEX idx_test_methods_type ON test_methods(method_type);

CREATE INDEX idx_test_specifications_sample_type ON test_specifications(sample_type_id);
CREATE INDEX idx_test_specifications_method ON test_specifications(test_method_id);
CREATE INDEX idx_test_specifications_parameter ON test_specifications(parameter_name);

CREATE INDEX idx_instruments_instrument_id ON instruments(instrument_id);
CREATE INDEX idx_instruments_status ON instruments(status);
CREATE INDEX idx_instruments_calibration_due ON instruments(next_calibration_due);
CREATE INDEX idx_instruments_location ON instruments(location);
CREATE INDEX idx_instruments_department ON instruments(department);

CREATE INDEX idx_test_executions_execution_id ON test_executions(execution_id);
CREATE INDEX idx_test_executions_sample ON test_executions(sample_id);
CREATE INDEX idx_test_executions_method ON test_executions(test_method_id);
CREATE INDEX idx_test_executions_analyst ON test_executions(analyst_id);
CREATE INDEX idx_test_executions_status ON test_executions(status);
CREATE INDEX idx_test_executions_start_date ON test_executions(start_datetime);
CREATE INDEX idx_test_executions_completion_date ON test_executions(completion_datetime);

CREATE INDEX idx_test_results_execution ON test_results(test_execution_id);
CREATE INDEX idx_test_results_specification ON test_results(test_specification_id);
CREATE INDEX idx_test_results_parameter ON test_results(parameter_name);
CREATE INDEX idx_test_results_oos ON test_results(out_of_specification);
CREATE INDEX idx_test_results_created_date ON test_results(created_at);

CREATE INDEX idx_calibration_records_instrument ON calibration_records(instrument_id);
CREATE INDEX idx_calibration_records_cal_id ON calibration_records(calibration_id);
CREATE INDEX idx_calibration_records_date ON calibration_records(calibration_date);
CREATE INDEX idx_calibration_records_due_date ON calibration_records(next_due_date);

CREATE INDEX idx_lims_audit_entity ON lims_audit_log(entity_type, entity_id);
CREATE INDEX idx_lims_audit_user ON lims_audit_log(user_id);
CREATE INDEX idx_lims_audit_timestamp ON lims_audit_log(timestamp);

-- Create audit triggers for LIMS tables
SELECT create_audit_trigger('sample_types');
SELECT create_audit_trigger('samples');
SELECT create_audit_trigger('test_methods');
SELECT create_audit_trigger('test_specifications');
SELECT create_audit_trigger('instruments');
SELECT create_audit_trigger('test_executions');
SELECT create_audit_trigger('test_results');
SELECT create_audit_trigger('calibration_records');

-- Create updated_at triggers for LIMS tables
SELECT create_updated_at_trigger('sample_types');
SELECT create_updated_at_trigger('samples');
SELECT create_updated_at_trigger('test_methods');
SELECT create_updated_at_trigger('test_specifications');
SELECT create_updated_at_trigger('instruments');
SELECT create_updated_at_trigger('test_executions');
SELECT create_updated_at_trigger('test_results');
SELECT create_updated_at_trigger('calibration_records');

-- Add constraints for data integrity
ALTER TABLE test_specifications ADD CONSTRAINT check_limits 
    CHECK (upper_limit IS NULL OR lower_limit IS NULL OR upper_limit > lower_limit);

ALTER TABLE samples ADD CONSTRAINT check_expiry_date 
    CHECK (expiry_date IS NULL OR expiry_date > collection_date);

ALTER TABLE calibration_records ADD CONSTRAINT check_due_date 
    CHECK (next_due_date > calibration_date);

ALTER TABLE test_executions ADD CONSTRAINT check_completion_time 
    CHECK (completion_datetime IS NULL OR completion_datetime >= start_datetime);

-- Create views for common LIMS queries
CREATE VIEW v_active_samples AS
SELECT 
    s.id,
    s.sample_id,
    s.batch_lot_number,
    st.name as sample_type_name,
    st.category,
    s.status,
    s.received_date,
    s.storage_location,
    u.username as current_custodian,
    COUNT(te.id) as total_tests,
    COUNT(CASE WHEN te.status = 'completed' THEN 1 END) as completed_tests
FROM samples s
JOIN sample_types st ON s.sample_type_id = st.id
LEFT JOIN users u ON s.current_custodian_id = u.id
LEFT JOIN test_executions te ON s.id = te.sample_id
WHERE s.status IN ('received', 'in_testing', 'testing_complete')
GROUP BY s.id, s.sample_id, s.batch_lot_number, st.name, st.category, 
         s.status, s.received_date, s.storage_location, u.username;

CREATE VIEW v_overdue_tests AS
SELECT 
    te.id,
    te.execution_id,
    s.sample_id,
    tm.title as test_method,
    u.username as analyst,
    te.start_datetime,
    te.status,
    EXTRACT(EPOCH FROM (NOW() - te.start_datetime))/3600 as hours_overdue
FROM test_executions te
JOIN samples s ON te.sample_id = s.id
JOIN test_methods tm ON te.test_method_id = tm.id
JOIN users u ON te.analyst_id = u.id
WHERE te.status IN ('pending', 'in_progress')
  AND te.start_datetime < NOW() - INTERVAL '24 hours';

CREATE VIEW v_oos_results AS
SELECT 
    tr.id,
    s.sample_id,
    s.batch_lot_number,
    tm.title as test_method,
    tr.parameter_name,
    tr.result_value,
    ts.lower_limit,
    ts.upper_limit,
    tr.created_at,
    u.username as analyst
FROM test_results tr
JOIN test_executions te ON tr.test_execution_id = te.id
JOIN samples s ON te.sample_id = s.id
JOIN test_methods tm ON te.test_method_id = tm.id
JOIN test_specifications ts ON tr.test_specification_id = ts.id
JOIN users u ON te.analyst_id = u.id
WHERE tr.out_of_specification = TRUE
ORDER BY tr.created_at DESC;

CREATE VIEW v_instrument_status AS
SELECT 
    i.id,
    i.instrument_id,
    i.name,
    i.location,
    i.status,
    i.next_calibration_due,
    CASE 
        WHEN i.next_calibration_due <= CURRENT_DATE THEN 'OVERDUE'
        WHEN i.next_calibration_due <= CURRENT_DATE + INTERVAL '30 days' THEN 'DUE_SOON'
        ELSE 'CURRENT'
    END as calibration_status,
    cr.calibration_date as last_calibration,
    cr.overall_result as last_calibration_result
FROM instruments i
LEFT JOIN LATERAL (
    SELECT calibration_date, overall_result
    FROM calibration_records 
    WHERE instrument_id = i.id 
    ORDER BY calibration_date DESC 
    LIMIT 1
) cr ON true;

-- Add comments for documentation
COMMENT ON TABLE sample_types IS 'Laboratory sample type definitions and requirements';
COMMENT ON TABLE samples IS 'Individual sample tracking with chain of custody';
COMMENT ON TABLE test_methods IS 'Analytical test procedures and methods';
COMMENT ON TABLE test_specifications IS 'Acceptance criteria and specification limits';
COMMENT ON TABLE instruments IS 'Laboratory equipment and instrumentation registry';
COMMENT ON TABLE test_executions IS 'Individual test run tracking and execution';
COMMENT ON TABLE test_results IS 'Test result data with compliance checking';
COMMENT ON TABLE calibration_records IS 'Instrument calibration tracking and compliance';
COMMENT ON TABLE lims_audit_log IS 'Specialized audit log for LIMS data integrity';

-- Create indexes on JSONB columns for better performance
CREATE INDEX idx_samples_chain_of_custody_gin ON samples USING GIN (chain_of_custody);
CREATE INDEX idx_test_methods_qualifications_gin ON test_methods USING GIN (analyst_qualifications);
CREATE INDEX idx_test_results_replicates_gin ON test_results USING GIN (replicate_values);
CREATE INDEX idx_instruments_specs_gin ON instruments USING GIN (specifications);

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO qms_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO qms_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO qms_readonly;