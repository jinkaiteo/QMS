-- LIMS Sample Data for Production Deployment
-- Phase 5 Implementation - QMS Platform v3.0

-- Insert Sample Types
INSERT INTO sample_types (code, name, category, description, storage_temperature_min, storage_temperature_max, storage_conditions, shelf_life_days, regulatory_category, created_by) VALUES
('API-001', 'Active Pharmaceutical Ingredient', 'raw_material', 'Raw API materials for drug manufacturing', 15, 25, 'Store in dry conditions, protect from light', 730, 'ICH Q3A', 1),
('EXC-001', 'Pharmaceutical Excipients', 'raw_material', 'Inactive ingredients for formulation', 15, 30, 'Store in original container', 1095, 'USP/NF', 1),
('FP-TAB', 'Finished Product - Tablets', 'finished_product', 'Finished tablet products for release testing', 15, 25, 'Store in original packaging', 1095, 'ICH Q6A', 1),
('FP-CAP', 'Finished Product - Capsules', 'finished_product', 'Finished capsule products for release testing', 15, 25, 'Store in original packaging', 1095, 'ICH Q6A', 1),
('WIP-001', 'Work in Process', 'in_process', 'In-process control samples', 15, 25, 'Immediate testing required', 7, 'Internal', 1),
('STAB-001', 'Stability Study Samples', 'stability', 'Long-term stability study samples', -20, 40, 'Controlled environment storage', 2190, 'ICH Q1A', 1),
('REF-STD', 'Reference Standards', 'reference_standard', 'Primary and secondary reference standards', 2, 8, 'Refrigerated storage, protect from light', 1825, 'USP', 1),
('ENV-001', 'Environmental Monitoring', 'environmental', 'Environmental monitoring samples', 15, 25, 'Process immediately', 1, 'Internal', 1);

-- Insert Test Methods
INSERT INTO test_methods (method_code, title, version, description, method_type, estimated_duration_hours, validation_status, effective_date, equipment_required, analyst_qualifications, created_by) VALUES
('HPLC-001', 'HPLC Assay for API Content', '2.1', 'High Performance Liquid Chromatography method for API quantification', 'HPLC', 4.0, 'approved', NOW(), '["HPLC System", "UV Detector", "C18 Column"]', '["HPLC Training", "Method Validation"]', 1),
('UV-001', 'UV Spectrophotometry Assay', '1.5', 'UV-Vis spectrophotometric analysis for API content', 'UV-VIS', 2.0, 'approved', NOW(), '["UV-Vis Spectrophotometer", "Quartz Cuvettes"]', '["UV Spectroscopy Training"]', 1),
('DISSOLVE-001', 'Dissolution Testing', '3.0', 'In-vitro dissolution testing for solid dosage forms', 'DISSOLUTION', 6.0, 'approved', NOW(), '["Dissolution Apparatus", "UV Detector", "Water Bath"]', '["Dissolution Training", "USP Methods"]', 1),
('MOISTURE-001', 'Karl Fischer Moisture Content', '1.2', 'Moisture determination by Karl Fischer titration', 'KF-TITRATION', 1.5, 'approved', NOW(), '["Karl Fischer Titrator", "Anhydrous Methanol"]', '["KF Titration Training"]', 1),
('MICROB-001', 'Microbial Limits Testing', '2.0', 'Microbiological examination for total viable count', 'MICROBIOLOGY', 48.0, 'approved', NOW(), '["Laminar Flow Hood", "Incubator", "Petri Dishes"]', '["Microbiology Training", "Aseptic Technique"]', 1),
('IDENT-001', 'Identity Testing by FTIR', '1.8', 'Identity confirmation using Fourier Transform Infrared Spectroscopy', 'FTIR', 1.0, 'approved', NOW(), '["FTIR Spectrometer", "ATR Accessory"]', '["FTIR Training", "Spectral Interpretation"]', 1),
('IMP-001', 'Related Substances by HPLC', '2.5', 'Determination of related substances and impurities', 'HPLC', 5.0, 'approved', NOW(), '["HPLC System", "PDA Detector", "C18 Column"]', '["HPLC Training", "Impurity Analysis"]', 1),
('HARDNESS-001', 'Tablet Hardness Testing', '1.0', 'Mechanical strength testing of tablets', 'PHYSICAL', 0.5, 'approved', NOW(), '["Hardness Tester"]', '["Physical Testing Training"]', 1);

-- Insert Test Specifications
INSERT INTO test_specifications (sample_type_id, test_method_id, parameter_name, specification_type, lower_limit, upper_limit, target_value, units, regulatory_requirement, criticality_level, statistical_approach, created_by) VALUES
-- API Testing Specifications
(1, 1, 'Assay (HPLC)', 'range', 98.0, 102.0, 100.0, '% w/w', true, 'critical', 'n=1', 1),
(1, 4, 'Moisture Content', 'limit', null, 0.5, null, '% w/w', true, 'critical', 'n=1', 1),
(1, 6, 'Identity', 'conformance', null, null, null, 'Pass/Fail', true, 'critical', 'n=1', 1),
(1, 7, 'Related Substances', 'limit', null, 0.5, null, '% total', true, 'critical', 'n=1', 1),

-- Finished Product Tablet Specifications
(3, 1, 'Assay (HPLC)', 'range', 95.0, 105.0, 100.0, '% label claim', true, 'critical', 'n=1', 1),
(3, 3, 'Dissolution', 'limit', 80.0, null, null, '% in 30 min', true, 'critical', 'n=6', 1),
(3, 8, 'Hardness', 'range', 4.0, 10.0, 7.0, 'kp', false, 'normal', 'n=10', 1),
(3, 6, 'Identity', 'conformance', null, null, null, 'Pass/Fail', true, 'critical', 'n=1', 1),

-- Finished Product Capsule Specifications
(4, 1, 'Assay (HPLC)', 'range', 95.0, 105.0, 100.0, '% label claim', true, 'critical', 'n=1', 1),
(4, 3, 'Dissolution', 'limit', 75.0, null, null, '% in 45 min', true, 'critical', 'n=6', 1),
(4, 6, 'Identity', 'conformance', null, null, null, 'Pass/Fail', true, 'critical', 'n=1', 1),

-- Reference Standard Specifications
(7, 2, 'Assay (UV)', 'range', 99.5, 100.5, 100.0, '% w/w', true, 'critical', 'n=3', 1),
(7, 4, 'Moisture Content', 'limit', null, 0.2, null, '% w/w', true, 'critical', 'n=1', 1),

-- Environmental Monitoring Specifications
(8, 5, 'Total Viable Count', 'limit', null, 100.0, null, 'CFU/plate', true, 'critical', 'n=3', 1);

-- Insert Instruments
INSERT INTO instruments (instrument_id, name, manufacturer, model, serial_number, location, department, calibration_frequency_days, specifications, created_by) VALUES
('HPLC-01', 'HPLC System 1', 'Waters Corporation', 'Alliance e2695', 'WAT123456', 'QC Lab - Room 201', 'Quality Control', 365, '{"pump_pressure_range": "0-6000 psi", "detector_wavelength": "190-800 nm"}', 1),
('HPLC-02', 'HPLC System 2', 'Agilent Technologies', '1260 Infinity II', 'AGI789012', 'QC Lab - Room 202', 'Quality Control', 365, '{"pump_pressure_range": "0-6000 psi", "detector_wavelength": "190-800 nm"}', 1),
('UV-01', 'UV-Vis Spectrophotometer', 'PerkinElmer', 'Lambda 365', 'PE345678', 'QC Lab - Room 203', 'Quality Control', 365, '{"wavelength_range": "190-1100 nm", "bandwidth": "1 nm"}', 1),
('DISS-01', 'Dissolution Apparatus', 'Agilent Technologies', '708-DS', 'AGI901234', 'QC Lab - Room 204', 'Quality Control', 365, '{"vessels": 8, "temperature_range": "35-42 C"}', 1),
('KF-01', 'Karl Fischer Titrator', 'Metrohm', '915 KF Ti-Touch', 'MET567890', 'QC Lab - Room 205', 'Quality Control', 180, '{"measurement_range": "10 ppm - 100%", "accuracy": "±0.1%"}', 1),
('FTIR-01', 'FTIR Spectrometer', 'PerkinElmer', 'Spectrum Two', 'PE123789', 'QC Lab - Room 206', 'Quality Control', 365, '{"wavenumber_range": "4000-400 cm-1", "resolution": "0.5 cm-1"}', 1),
('HARD-01', 'Tablet Hardness Tester', 'Erweka', 'TBH 125', 'ERW456123', 'QC Lab - Room 207', 'Quality Control', 180, '{"force_range": "0-300 N", "accuracy": "±1%"}', 1),
('BAL-01', 'Analytical Balance', 'Mettler Toledo', 'XPE205', 'MT789456', 'QC Lab - Room 201', 'Quality Control', 365, '{"capacity": "220 g", "readability": "0.01 mg"}', 1);

-- Insert Sample Calibration Records
INSERT INTO calibration_records (calibration_id, instrument_id, calibration_date, next_due_date, calibration_type, calibration_standard, accuracy_check, precision_check, linearity_check, overall_result, performed_by_id, created_by) VALUES
('CAL-2024-HPLC01-001', 1, '2024-01-15', '2025-01-15', 'Annual Calibration', 'Caffeine USP RS', true, true, true, 'PASS', 1, 1),
('CAL-2024-HPLC02-001', 2, '2024-01-20', '2025-01-20', 'Annual Calibration', 'Caffeine USP RS', true, true, true, 'PASS', 1, 1),
('CAL-2024-UV01-001', 3, '2024-02-01', '2025-02-01', 'Annual Calibration', 'Holmium Oxide Filter', true, true, true, 'PASS', 1, 1),
('CAL-2024-DISS01-001', 4, '2024-02-15', '2025-02-15', 'Annual Calibration', 'Salicylic Acid Tablets', true, true, true, 'PASS', 1, 1),
('CAL-2024-KF01-001', 5, '2024-03-01', '2024-08-28', 'Semi-Annual', 'Water Standard', true, true, true, 'PASS', 1, 1),
('CAL-2024-FTIR01-001', 6, '2024-03-15', '2025-03-15', 'Annual Calibration', 'Polystyrene Film', true, true, true, 'PASS', 1, 1),
('CAL-2024-HARD01-001', 7, '2024-04-01', '2024-09-28', 'Semi-Annual', 'Reference Weight Set', true, true, true, 'PASS', 1, 1),
('CAL-2024-BAL01-001', 8, '2024-04-15', '2025-04-15', 'Annual Calibration', 'Class E2 Weights', true, true, true, 'PASS', 1, 1);

-- Insert Sample Samples for Testing
INSERT INTO samples (sample_id, sample_type_id, batch_lot_number, collection_date, received_by_id, current_custodian_id, storage_location, collected_by, priority_level, created_by) VALUES
('API-2024-001', 1, 'API-LOT-240101', '2024-11-01 08:00:00+00', 2, 2, 'Warehouse A-101', 'Supplier QC', 'normal', 1),
('API-2024-002', 1, 'API-LOT-240102', '2024-11-01 08:30:00+00', 2, 2, 'Warehouse A-102', 'Supplier QC', 'high', 1),
('FP-2024-001', 3, 'TAB-LOT-240301', '2024-11-01 09:00:00+00', 2, 2, 'QC Sample Room', 'Production Line 1', 'normal', 1),
('FP-2024-002', 4, 'CAP-LOT-240401', '2024-11-01 09:30:00+00', 2, 2, 'QC Sample Room', 'Production Line 2', 'normal', 1),
('STAB-2024-001', 6, 'STAB-LOT-240601', '2024-11-01 10:00:00+00', 2, 2, 'Stability Chamber 1', 'Stability Coordinator', 'normal', 1),
('REF-2024-001', 7, 'REF-STD-240701', '2024-11-01 10:30:00+00', 2, 2, 'Reference Storage', 'Standards Manager', 'high', 1);

-- Insert Test Executions
INSERT INTO test_executions (execution_id, sample_id, test_method_id, analyst_id, start_datetime, status, instrument_id, created_by) VALUES
('EXE-20241101-001', 1, 1, 2, '2024-11-01 14:00:00+00', 'completed', 1, 1),
('EXE-20241101-002', 1, 4, 2, '2024-11-01 15:30:00+00', 'completed', 5, 1),
('EXE-20241101-003', 1, 6, 2, '2024-11-01 16:00:00+00', 'completed', 6, 1),
('EXE-20241101-004', 3, 1, 2, '2024-11-01 14:30:00+00', 'in_progress', 2, 1),
('EXE-20241101-005', 3, 3, 2, '2024-11-01 15:00:00+00', 'pending', 4, 1),
('EXE-20241101-006', 6, 2, 2, '2024-11-01 16:30:00+00', 'pending', 3, 1);

-- Insert Test Results
INSERT INTO test_results (test_execution_id, test_specification_id, parameter_name, result_value, units, pass_fail, out_of_specification, created_by) VALUES
-- API Assay Results
(1, 1, 'Assay (HPLC)', 99.8, '% w/w', true, false, 1),
-- API Moisture Results
(2, 2, 'Moisture Content', 0.3, '% w/w', true, false, 1),
-- API Identity Results  
(3, 3, 'Identity', null, 'Pass/Fail', true, false, 1);

-- Update test execution completion times for completed tests
UPDATE test_executions SET 
    completion_datetime = start_datetime + INTERVAL '4 hours',
    status = 'completed'
WHERE status = 'completed';

-- Update result text for identity test
UPDATE test_results SET result_text = 'PASS - Spectrum matches reference standard' 
WHERE parameter_name = 'Identity';

-- Insert some chain of custody data
UPDATE samples SET chain_of_custody = jsonb_build_object(
    'events', jsonb_build_array(
        jsonb_build_object(
            'timestamp', '2024-11-01T08:00:00Z',
            'event_type', 'RECEIVED',
            'user_id', 2,
            'location', storage_location,
            'notes', 'Sample received and logged into LIMS'
        )
    )
) WHERE id <= 6;

-- Create some upcoming calibration due dates for testing
UPDATE instruments SET 
    next_calibration_due = CURRENT_DATE + INTERVAL '30 days'
WHERE instrument_id IN ('KF-01', 'HARD-01');

UPDATE instruments SET 
    next_calibration_due = CURRENT_DATE - INTERVAL '5 days',
    status = 'calibration_due'
WHERE instrument_id = 'BAL-01';

-- Insert LIMS audit log entries for testing
INSERT INTO lims_audit_log (entity_type, entity_id, action, new_values, user_id, ip_address) VALUES
('Sample', 1, 'REGISTER', '{"sample_id": "API-2024-001", "status": "received"}', 1, '192.168.1.100'),
('TestExecution', 1, 'START', '{"execution_id": "EXE-20241101-001", "status": "pending"}', 2, '192.168.1.101'),
('TestResult', 1, 'RECORD', '{"parameter_name": "Assay (HPLC)", "result_value": 99.8}', 2, '192.168.1.101'),
('Instrument', 8, 'CALIBRATION_DUE', '{"status": "calibration_due"}', 1, '192.168.1.100');