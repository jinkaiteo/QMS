-- Training Management System Sample Data
-- Phase 4 Implementation - QMS Platform v3.0

-- Insert core competencies
INSERT INTO competencies (code, name, description, category, created_by) VALUES
('GMP-001', 'Good Manufacturing Practices', 'Understanding of GMP principles and regulations', 'Regulatory', 1),
('GDP-001', 'Good Documentation Practices', 'Proper documentation standards and procedures', 'Quality', 1),
('SAFETY-001', 'Laboratory Safety', 'Basic laboratory safety procedures and emergency protocols', 'Safety', 1),
('LEAN-001', 'Lean Manufacturing', 'Lean principles and waste reduction techniques', 'Process', 1),
('CAPA-001', 'CAPA Management', 'Corrective and Preventive Action procedures', 'Quality', 1),
('AUDIT-001', 'Internal Auditing', 'Internal audit principles and execution', 'Quality', 1),
('RISK-001', 'Risk Assessment', 'Risk identification and mitigation strategies', 'Quality', 1),
('LEADERSHIP-001', 'Team Leadership', 'Leadership and team management skills', 'Leadership', 1),
('COMMUNICATION-001', 'Effective Communication', 'Professional communication skills', 'Soft Skills', 1),
('PROBLEM-001', 'Problem Solving', 'Systematic problem-solving methodologies', 'Analytical', 1);

-- Insert training programs
INSERT INTO training_programs (
    code, title, description, training_type, delivery_method, 
    duration_hours, validity_months, regulatory_requirement,
    learning_objectives, prerequisites, created_by
) VALUES
('TRN-GMP-001', 'GMP Fundamentals', 'Basic Good Manufacturing Practices training for all personnel', 
 'compliance', 'blended', 8.0, 12, true,
 '["Understand GMP principles", "Identify contamination risks", "Follow proper procedures"]',
 '["Employee onboarding complete"]', 1),

('TRN-GDP-001', 'Documentation Best Practices', 'Training on proper documentation standards',
 'compliance', 'online', 4.0, 24, true,
 '["Create compliant documentation", "Review and approve documents", "Maintain records"]',
 '["GMP Fundamentals completed"]', 1),

('TRN-SAFETY-001', 'Laboratory Safety Training', 'Comprehensive laboratory safety training',
 'safety', 'classroom', 6.0, 12, true,
 '["Identify safety hazards", "Use PPE correctly", "Respond to emergencies"]',
 '[]', 1),

('TRN-CAPA-001', 'CAPA Management Training', 'Training on CAPA system and procedures',
 'technical', 'blended', 12.0, 24, false,
 '["Investigate quality events", "Develop corrective actions", "Verify effectiveness"]',
 '["GMP Fundamentals completed", "GDP training completed"]', 1),

('TRN-AUDIT-001', 'Internal Audit Training', 'Training for internal auditors',
 'technical', 'classroom', 16.0, 36, false,
 '["Plan audit activities", "Conduct interviews", "Document findings"]',
 '["CAPA Management completed", "3+ years experience"]', 1),

('TRN-ONBOARD-001', 'New Employee Onboarding', 'Comprehensive onboarding for new hires',
 'onboarding', 'blended', 24.0, NULL, true,
 '["Company policies", "Safety procedures", "Job-specific training"]',
 '[]', 1),

('TRN-LEADERSHIP-001', 'Supervisory Leadership', 'Leadership training for supervisors',
 'leadership', 'classroom', 20.0, 36, false,
 '["Team management", "Performance coaching", "Conflict resolution"]',
 '["2+ years experience", "Supervisor role"]', 1),

('TRN-RISK-001', 'Risk Assessment Methods', 'Training on risk assessment techniques',
 'technical', 'online', 8.0, 24, false,
 '["Risk identification", "Risk analysis", "Risk mitigation planning"]',
 '["GMP Fundamentals completed"]', 1);

-- Map competencies to training programs
INSERT INTO competency_mappings (program_id, competency_id, competency_level) VALUES
-- GMP Fundamentals develops basic GMP competency
(1, 1, 'basic'),
-- Documentation training develops GDP competency
(2, 2, 'intermediate'),
-- Safety training develops safety competency
(3, 3, 'intermediate'),
-- CAPA training develops CAPA and problem-solving competencies
(4, 5, 'advanced'),
(4, 10, 'intermediate'),
-- Audit training develops audit competency
(5, 6, 'advanced'),
-- Leadership training develops leadership and communication
(7, 8, 'intermediate'),
(7, 9, 'intermediate'),
-- Risk training develops risk assessment competency
(8, 7, 'intermediate');

-- Insert role-based competency requirements (assuming roles exist)
-- Quality Assurance role requirements
INSERT INTO role_competencies (role_id, competency_id, required_level, critical) VALUES
(2, 1, 'advanced', true),   -- GMP - advanced level required
(2, 2, 'advanced', true),   -- GDP - advanced level required
(2, 5, 'advanced', true),   -- CAPA - advanced level required
(2, 6, 'intermediate', false), -- Audit - intermediate level
(2, 7, 'intermediate', true),   -- Risk - intermediate level required
(2, 9, 'intermediate', false);  -- Communication - intermediate level

-- Production role requirements
INSERT INTO role_competencies (role_id, competency_id, required_level, critical) VALUES
(3, 1, 'intermediate', true),   -- GMP - intermediate level required
(3, 2, 'basic', true),          -- GDP - basic level required
(3, 3, 'intermediate', true),   -- Safety - intermediate level required
(3, 4, 'basic', false);         -- Lean - basic level helpful

-- Create sample training sessions
INSERT INTO training_sessions (
    program_id, session_code, start_datetime, end_datetime, 
    location, max_participants, instructor_id, created_by
) VALUES
-- GMP training sessions
(1, 'GMP-2024-001', '2024-11-01 09:00:00+00', '2024-11-01 17:00:00+00', 
 'Training Room A', 20, 1, 1),
(1, 'GMP-2024-002', '2024-11-15 09:00:00+00', '2024-11-15 17:00:00+00', 
 'Training Room A', 20, 1, 1),

-- Safety training sessions
(3, 'SAFETY-2024-001', '2024-11-05 08:00:00+00', '2024-11-05 14:00:00+00', 
 'Laboratory', 12, 1, 1),
(3, 'SAFETY-2024-002', '2024-11-20 08:00:00+00', '2024-11-20 14:00:00+00', 
 'Laboratory', 12, 1, 1),

-- Leadership training
(7, 'LEAD-2024-001', '2024-11-10 09:00:00+00', '2024-11-12 17:00:00+00', 
 'Conference Room', 15, 1, 1);

-- Sample training assignments (assuming users exist)
INSERT INTO employee_training (
    employee_id, program_id, due_date, reason, assigned_by_id, created_by
) VALUES
-- Assign GMP training to multiple employees
(2, 1, '2024-12-01 23:59:59+00', 'Required for all QA personnel', 1, 1),
(3, 1, '2024-12-01 23:59:59+00', 'Required for production staff', 1, 1),

-- Assign safety training
(2, 3, '2024-11-30 23:59:59+00', 'Annual safety requirement', 1, 1),
(3, 3, '2024-11-30 23:59:59+00', 'Annual safety requirement', 1, 1),

-- Assign documentation training to QA
(2, 2, '2024-12-15 23:59:59+00', 'Role-specific requirement', 1, 1);

-- Insert sample competency assessments
INSERT INTO competency_assessments (
    employee_id, competency_id, assessor_id, assessment_date,
    current_level, target_level, assessment_method, 
    strengths, improvement_areas, recommended_training
) VALUES
(2, 1, 1, '2024-10-15', 'intermediate', 'advanced', 'Observation and interview',
 'Good understanding of basic principles', 'Needs more experience with deviations',
 '["CAPA Management Training"]'),

(3, 3, 1, '2024-10-10', 'basic', 'intermediate', 'Practical demonstration',
 'Follows safety procedures well', 'Needs training on emergency procedures',
 '["Laboratory Safety Training"]');

-- Add some training completions
UPDATE employee_training 
SET status = 'completed', 
    start_date = '2024-10-01 09:00:00+00',
    completion_date = '2024-10-01 17:00:00+00',
    score = 85.0,
    pass_fail = true,
    certificate_issued = true,
    certificate_number = 'CERT-2024-TRN-GMP-001-00002',
    certification_date = '2024-10-01 17:00:00+00',
    expiry_date = '2025-10-01 23:59:59+00'
WHERE employee_id = 2 AND program_id = 1;