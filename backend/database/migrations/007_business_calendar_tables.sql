-- Business Calendar System Tables - Phase B Sprint 2 Day 6
-- Advanced Scheduling & Business Calendar Integration

-- Business Hours Configuration Table
CREATE TABLE IF NOT EXISTS business_hours_config (
    id SERIAL PRIMARY KEY,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_business_day BOOLEAN DEFAULT TRUE,
    extended_hours_start TIME,
    extended_hours_end TIME,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_day_of_week UNIQUE (day_of_week)
);

-- Company Holidays Table
CREATE TABLE IF NOT EXISTS company_holidays (
    id SERIAL PRIMARY KEY,
    holiday_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    holiday_type VARCHAR(50) NOT NULL DEFAULT 'company',
    description TEXT,
    is_observed BOOLEAN DEFAULT TRUE,
    affects_delivery BOOLEAN DEFAULT TRUE,
    departments JSONB DEFAULT '[]',
    regions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_holiday_type CHECK (
        holiday_type IN ('federal', 'company', 'department', 'regional', 'floating', 'observance')
    )
);

-- Delivery Rules Configuration Table
CREATE TABLE IF NOT EXISTS delivery_rules_config (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    rule_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Business Calendar Events Table (for tracking special events)
CREATE TABLE IF NOT EXISTS business_calendar_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    event_type VARCHAR(50) NOT NULL DEFAULT 'business',
    affects_scheduling BOOLEAN DEFAULT FALSE,
    departments JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_event_type CHECK (
        event_type IN ('business', 'maintenance', 'training', 'audit', 'shutdown', 'special')
    ),
    CONSTRAINT valid_date_range CHECK (end_date IS NULL OR end_date >= start_date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_company_holidays_date ON company_holidays(date);
CREATE INDEX IF NOT EXISTS idx_company_holidays_type ON company_holidays(holiday_type);
CREATE INDEX IF NOT EXISTS idx_company_holidays_observed ON company_holidays(is_observed);
CREATE INDEX IF NOT EXISTS idx_business_calendar_events_date_range ON business_calendar_events(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_business_calendar_events_type ON business_calendar_events(event_type);
CREATE INDEX IF NOT EXISTS idx_delivery_rules_active ON delivery_rules_config(is_active);

-- Insert default business hours (Monday-Friday, 8 AM - 6 PM)
INSERT INTO business_hours_config (day_of_week, start_time, end_time, is_business_day, extended_hours_start, extended_hours_end)
VALUES 
    (0, '08:00:00', '18:00:00', TRUE, '07:00:00', '20:00:00'),  -- Monday
    (1, '08:00:00', '18:00:00', TRUE, '07:00:00', '20:00:00'),  -- Tuesday
    (2, '08:00:00', '18:00:00', TRUE, '07:00:00', '20:00:00'),  -- Wednesday
    (3, '08:00:00', '18:00:00', TRUE, '07:00:00', '20:00:00'),  -- Thursday
    (4, '08:00:00', '18:00:00', TRUE, '07:00:00', '20:00:00'),  -- Friday
    (5, '10:00:00', '14:00:00', FALSE, NULL, NULL),             -- Saturday (limited)
    (6, '00:00:00', '00:00:00', FALSE, NULL, NULL)              -- Sunday (closed)
ON CONFLICT (day_of_week) DO NOTHING;

-- Insert default delivery rules
INSERT INTO delivery_rules_config (rule_name, rule_value, description, is_active)
VALUES 
    ('allow_weekend_delivery', 'false', 'Allow report delivery on weekends', TRUE),
    ('allow_holiday_delivery', 'false', 'Allow report delivery on holidays', TRUE),
    ('emergency_override_allowed', 'true', 'Allow emergency override of delivery restrictions', TRUE),
    ('extended_hours_threshold', '"high_priority"', 'Priority level required for extended hours delivery', TRUE),
    ('business_day_rule', '"flexible"', 'Business day calculation rule (strict/flexible/extended)', TRUE),
    ('max_delivery_window_days', '14', 'Maximum days ahead for delivery scheduling', TRUE),
    ('default_delivery_time', '"08:00"', 'Default delivery time for scheduled reports', TRUE),
    ('weekend_processing_allowed', 'true', 'Allow report processing on weekends', TRUE),
    ('holiday_processing_allowed', 'false', 'Allow report processing on holidays', TRUE),
    ('auto_reschedule_holidays', 'true', 'Automatically reschedule deliveries that fall on holidays', TRUE)
ON CONFLICT (rule_name) DO NOTHING;

-- Insert sample company holidays
INSERT INTO company_holidays (holiday_id, name, date, holiday_type, description, is_observed, affects_delivery)
VALUES 
    ('company_2024_christmas_eve', 'Christmas Eve (Company)', '2024-12-24', 'company', 'Company observes Christmas Eve as a half day', TRUE, TRUE),
    ('company_2024_new_years_eve', 'New Year''s Eve (Company)', '2024-12-31', 'company', 'Company observes New Year''s Eve as a half day', TRUE, TRUE),
    ('company_2024_spring_break', 'Company Spring Break', '2024-03-25', 'company', 'Annual company spring break day', TRUE, TRUE),
    ('company_2024_summer_shutdown_start', 'Summer Shutdown Start', '2024-07-01', 'company', 'Beginning of summer maintenance shutdown', TRUE, TRUE),
    ('company_2024_summer_shutdown_end', 'Summer Shutdown End', '2024-07-05', 'company', 'End of summer maintenance shutdown', TRUE, TRUE),
    ('floating_2024_personal_day_1', 'Floating Personal Day 1', '2024-06-15', 'floating', 'Floating personal day option 1', FALSE, FALSE),
    ('floating_2024_personal_day_2', 'Floating Personal Day 2', '2024-09-15', 'floating', 'Floating personal day option 2', FALSE, FALSE)
ON CONFLICT (holiday_id) DO NOTHING;

-- Insert sample business calendar events
INSERT INTO business_calendar_events (event_id, title, description, start_date, end_date, event_type, affects_scheduling, created_by)
VALUES 
    ('audit_2024_q1', 'Q1 Internal Audit', 'Quality management system internal audit', '2024-03-15', '2024-03-17', 'audit', TRUE, 1),
    ('maintenance_2024_summer', 'Annual System Maintenance', 'Scheduled system maintenance and upgrades', '2024-07-01', '2024-07-05', 'maintenance', TRUE, 1),
    ('training_2024_gmp', 'GMP Training Week', 'Good Manufacturing Practices training for all staff', '2024-05-20', '2024-05-24', 'training', TRUE, 1),
    ('shutdown_2024_year_end', 'Year-end Shutdown', 'Annual year-end facility shutdown', '2024-12-25', '2024-01-02', 'shutdown', TRUE, 1)
ON CONFLICT (event_id) DO NOTHING;

-- Update triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers
DROP TRIGGER IF EXISTS business_hours_config_update_trigger ON business_hours_config;
CREATE TRIGGER business_hours_config_update_trigger
    BEFORE UPDATE ON business_hours_config
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS company_holidays_update_trigger ON company_holidays;
CREATE TRIGGER company_holidays_update_trigger
    BEFORE UPDATE ON company_holidays
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS delivery_rules_config_update_trigger ON delivery_rules_config;
CREATE TRIGGER delivery_rules_config_update_trigger
    BEFORE UPDATE ON delivery_rules_config
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS business_calendar_events_update_trigger ON business_calendar_events;
CREATE TRIGGER business_calendar_events_update_trigger
    BEFORE UPDATE ON business_calendar_events
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Views for easy data access
CREATE OR REPLACE VIEW v_active_company_holidays AS
SELECT 
    holiday_id,
    name,
    date,
    holiday_type,
    description,
    affects_delivery,
    departments,
    regions
FROM company_holidays 
WHERE is_observed = TRUE 
ORDER BY date;

CREATE OR REPLACE VIEW v_business_hours_summary AS
SELECT 
    day_of_week,
    CASE day_of_week 
        WHEN 0 THEN 'Monday'
        WHEN 1 THEN 'Tuesday'
        WHEN 2 THEN 'Wednesday'
        WHEN 3 THEN 'Thursday'
        WHEN 4 THEN 'Friday'
        WHEN 5 THEN 'Saturday'
        WHEN 6 THEN 'Sunday'
    END as day_name,
    start_time,
    end_time,
    is_business_day,
    extended_hours_start,
    extended_hours_end,
    CASE 
        WHEN is_business_day THEN 'Business Day'
        WHEN extended_hours_start IS NOT NULL THEN 'Limited Hours'
        ELSE 'Closed'
    END as status
FROM business_hours_config
ORDER BY day_of_week;

CREATE OR REPLACE VIEW v_upcoming_calendar_events AS
SELECT 
    event_id,
    title,
    description,
    start_date,
    end_date,
    event_type,
    affects_scheduling,
    CASE 
        WHEN end_date IS NULL THEN 1
        ELSE (end_date - start_date + 1)
    END as duration_days
FROM business_calendar_events 
WHERE start_date >= CURRENT_DATE 
ORDER BY start_date;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON business_hours_config TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON company_holidays TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON delivery_rules_config TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON business_calendar_events TO qms_user;
GRANT SELECT ON v_active_company_holidays TO qms_user;
GRANT SELECT ON v_business_hours_summary TO qms_user;
GRANT SELECT ON v_upcoming_calendar_events TO qms_user;
GRANT USAGE ON SEQUENCE business_hours_config_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE company_holidays_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE delivery_rules_config_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE business_calendar_events_id_seq TO qms_user;