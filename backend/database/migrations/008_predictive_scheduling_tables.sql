-- Predictive Scheduling Analytics Tables - Phase B Sprint 2 Day 6 Option B
-- Machine Learning and Predictive Analytics Database Schema

-- ML Training Data Table
CREATE TABLE IF NOT EXISTS ml_training_data (
    id SERIAL PRIMARY KEY,
    training_id VARCHAR(100) NOT NULL UNIQUE,
    features JSONB NOT NULL,
    target_value REAL NOT NULL,
    data_source VARCHAR(100) NOT NULL,
    quality_score REAL DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_quality_score CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    CONSTRAINT valid_target_value CHECK (target_value >= 0.0 AND target_value <= 24.0)
);

-- Prediction Results Table
CREATE TABLE IF NOT EXISTS prediction_results (
    id SERIAL PRIMARY KEY,
    prediction_id VARCHAR(100) NOT NULL UNIQUE,
    request_data JSONB NOT NULL,
    predicted_time TIMESTAMP WITH TIME ZONE NOT NULL,
    confidence_score REAL NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    optimization_factors JSONB DEFAULT '[]',
    alternative_times JSONB DEFAULT '[]',
    capacity_impact JSONB DEFAULT '{}',
    risk_assessment JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
);

-- Prediction Feedback Table
CREATE TABLE IF NOT EXISTS prediction_feedback (
    id SERIAL PRIMARY KEY,
    feedback_id VARCHAR(100) NOT NULL UNIQUE,
    prediction_id VARCHAR(100) NOT NULL,
    actual_outcome JSONB NOT NULL,
    feedback_score REAL NOT NULL,
    actual_delivery_time TIMESTAMP WITH TIME ZONE,
    success_indicator BOOLEAN,
    performance_metrics JSONB DEFAULT '{}',
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_feedback_score CHECK (feedback_score >= 0.0 AND feedback_score <= 1.0),
    CONSTRAINT fk_prediction FOREIGN KEY (prediction_id) REFERENCES prediction_results(prediction_id) ON DELETE CASCADE
);

-- ML Model Performance Table
CREATE TABLE IF NOT EXISTS ml_model_performance (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    accuracy REAL NOT NULL,
    precision_score REAL,
    recall_score REAL,
    f1_score REAL,
    mean_absolute_error REAL,
    root_mean_square_error REAL,
    training_samples INTEGER NOT NULL,
    validation_samples INTEGER,
    hyperparameters JSONB DEFAULT '{}',
    feature_importance JSONB DEFAULT '{}',
    training_duration_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT valid_accuracy CHECK (accuracy >= 0.0 AND accuracy <= 1.0),
    CONSTRAINT valid_training_samples CHECK (training_samples >= 0),
    CONSTRAINT unique_active_model UNIQUE (model_type, is_active) DEFERRABLE INITIALLY DEFERRED
);

-- Pattern Analysis Results Table
CREATE TABLE IF NOT EXISTS pattern_analysis_results (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(100) NOT NULL UNIQUE,
    analysis_type VARCHAR(50) NOT NULL,
    scope_department VARCHAR(100),
    analysis_period_start DATE NOT NULL,
    analysis_period_end DATE NOT NULL,
    total_samples INTEGER NOT NULL,
    success_rate REAL NOT NULL,
    peak_hours JSONB DEFAULT '[]',
    seasonal_trends JSONB DEFAULT '{}',
    department_preferences JSONB DEFAULT '{}',
    optimization_opportunities JSONB DEFAULT '[]',
    insights JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
    CONSTRAINT valid_period CHECK (analysis_period_end >= analysis_period_start)
);

-- Capacity Forecasts Table
CREATE TABLE IF NOT EXISTS capacity_forecasts (
    id SERIAL PRIMARY KEY,
    forecast_id VARCHAR(100) NOT NULL UNIQUE,
    forecast_date DATE NOT NULL,
    forecast_period_days INTEGER NOT NULL,
    predicted_deliveries INTEGER NOT NULL,
    predicted_utilization REAL NOT NULL,
    peak_risk_score REAL NOT NULL,
    bottleneck_probability REAL NOT NULL,
    confidence_score REAL NOT NULL,
    daily_forecasts JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    model_used VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_utilization CHECK (predicted_utilization >= 0.0 AND predicted_utilization <= 2.0),
    CONSTRAINT valid_risk_scores CHECK (
        peak_risk_score >= 0.0 AND peak_risk_score <= 1.0 AND
        bottleneck_probability >= 0.0 AND bottleneck_probability <= 1.0 AND
        confidence_score >= 0.0 AND confidence_score <= 1.0
    )
);

-- Schedule Optimizations Table
CREATE TABLE IF NOT EXISTS schedule_optimizations (
    id SERIAL PRIMARY KEY,
    optimization_id VARCHAR(100) NOT NULL UNIQUE,
    target_date DATE NOT NULL,
    optimization_goal VARCHAR(50) NOT NULL,
    current_schedule JSONB NOT NULL,
    optimized_schedule JSONB NOT NULL,
    improvement_metrics JSONB DEFAULT '{}',
    implementation_effort VARCHAR(20),
    expected_benefits JSONB DEFAULT '[]',
    identified_risks JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'proposed',
    applied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    
    CONSTRAINT valid_status CHECK (status IN ('proposed', 'approved', 'applied', 'rejected')),
    CONSTRAINT valid_effort CHECK (implementation_effort IN ('low', 'medium', 'high', 'critical'))
);

-- Feature Importance Tracking Table
CREATE TABLE IF NOT EXISTS feature_importance_tracking (
    id SERIAL PRIMARY KEY,
    tracking_id VARCHAR(100) NOT NULL UNIQUE,
    model_type VARCHAR(50) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    importance_score REAL NOT NULL,
    trend_direction VARCHAR(10),
    stability_score REAL,
    measurement_date DATE NOT NULL,
    sample_size INTEGER,
    confidence_level REAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_importance CHECK (importance_score >= 0.0 AND importance_score <= 1.0),
    CONSTRAINT valid_trend CHECK (trend_direction IN ('increasing', 'decreasing', 'stable', 'volatile'))
);

-- Scheduling Insights Table
CREATE TABLE IF NOT EXISTS scheduling_insights (
    id SERIAL PRIMARY KEY,
    insight_id VARCHAR(100) NOT NULL UNIQUE,
    insight_type VARCHAR(50) NOT NULL,
    scope_department VARCHAR(100),
    analysis_period_days INTEGER NOT NULL,
    executive_summary JSONB DEFAULT '{}',
    key_findings JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    trend_analysis JSONB DEFAULT '{}',
    alerts JSONB DEFAULT '[]',
    priority_level VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'active',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    
    CONSTRAINT valid_priority CHECK (priority_level IN ('low', 'normal', 'high', 'critical')),
    CONSTRAINT valid_insight_status CHECK (status IN ('active', 'archived', 'superseded'))
);

-- Indexes for Performance Optimization
CREATE INDEX IF NOT EXISTS idx_ml_training_data_created_at ON ml_training_data(created_at);
CREATE INDEX IF NOT EXISTS idx_ml_training_data_source ON ml_training_data(data_source);
CREATE INDEX IF NOT EXISTS idx_ml_training_data_quality ON ml_training_data(quality_score) WHERE quality_score >= 0.8;

CREATE INDEX IF NOT EXISTS idx_prediction_results_created_at ON prediction_results(created_at);
CREATE INDEX IF NOT EXISTS idx_prediction_results_model ON prediction_results(model_used);
CREATE INDEX IF NOT EXISTS idx_prediction_results_confidence ON prediction_results(confidence_score);

CREATE INDEX IF NOT EXISTS idx_prediction_feedback_prediction_id ON prediction_feedback(prediction_id);
CREATE INDEX IF NOT EXISTS idx_prediction_feedback_score ON prediction_feedback(feedback_score);
CREATE INDEX IF NOT EXISTS idx_prediction_feedback_created_at ON prediction_feedback(created_at);

CREATE INDEX IF NOT EXISTS idx_ml_model_performance_type ON ml_model_performance(model_type);
CREATE INDEX IF NOT EXISTS idx_ml_model_performance_active ON ml_model_performance(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_ml_model_performance_accuracy ON ml_model_performance(accuracy);

CREATE INDEX IF NOT EXISTS idx_pattern_analysis_type ON pattern_analysis_results(analysis_type);
CREATE INDEX IF NOT EXISTS idx_pattern_analysis_department ON pattern_analysis_results(scope_department);
CREATE INDEX IF NOT EXISTS idx_pattern_analysis_period ON pattern_analysis_results(analysis_period_start, analysis_period_end);

CREATE INDEX IF NOT EXISTS idx_capacity_forecasts_date ON capacity_forecasts(forecast_date);
CREATE INDEX IF NOT EXISTS idx_capacity_forecasts_confidence ON capacity_forecasts(confidence_score);

CREATE INDEX IF NOT EXISTS idx_schedule_optimizations_date ON schedule_optimizations(target_date);
CREATE INDEX IF NOT EXISTS idx_schedule_optimizations_status ON schedule_optimizations(status);
CREATE INDEX IF NOT EXISTS idx_schedule_optimizations_goal ON schedule_optimizations(optimization_goal);

CREATE INDEX IF NOT EXISTS idx_feature_importance_model ON feature_importance_tracking(model_type);
CREATE INDEX IF NOT EXISTS idx_feature_importance_feature ON feature_importance_tracking(feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_importance_date ON feature_importance_tracking(measurement_date);

CREATE INDEX IF NOT EXISTS idx_scheduling_insights_type ON scheduling_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_scheduling_insights_department ON scheduling_insights(scope_department);
CREATE INDEX IF NOT EXISTS idx_scheduling_insights_priority ON scheduling_insights(priority_level);
CREATE INDEX IF NOT EXISTS idx_scheduling_insights_status ON scheduling_insights(status) WHERE status = 'active';

-- Specialized Indexes for Analytics Queries
CREATE INDEX IF NOT EXISTS idx_prediction_accuracy_analysis ON prediction_feedback(
    prediction_id, feedback_score, created_at
);

CREATE INDEX IF NOT EXISTS idx_model_comparison ON ml_model_performance(
    model_type, accuracy, created_at
) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_temporal_patterns ON prediction_results(
    date_trunc('hour', predicted_time), confidence_score
);

-- Views for Analytics and Reporting

-- View: Model Performance Summary
CREATE OR REPLACE VIEW v_model_performance_summary AS
SELECT 
    model_type,
    COUNT(*) as total_models,
    AVG(accuracy) as avg_accuracy,
    MAX(accuracy) as best_accuracy,
    AVG(training_samples) as avg_training_samples,
    MAX(created_at) as latest_training
FROM ml_model_performance 
WHERE is_active = TRUE
GROUP BY model_type;

-- View: Prediction Accuracy Trends
CREATE OR REPLACE VIEW v_prediction_accuracy_trends AS
SELECT 
    pr.model_used,
    DATE_TRUNC('week', pr.created_at) as week,
    COUNT(*) as total_predictions,
    AVG(pf.feedback_score) as avg_accuracy,
    STDDEV(pf.feedback_score) as accuracy_variance
FROM prediction_results pr
JOIN prediction_feedback pf ON pr.prediction_id = pf.prediction_id
WHERE pr.created_at >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY pr.model_used, DATE_TRUNC('week', pr.created_at)
ORDER BY week DESC;

-- View: Feature Importance Rankings
CREATE OR REPLACE VIEW v_feature_importance_rankings AS
SELECT 
    model_type,
    feature_name,
    AVG(importance_score) as avg_importance,
    COUNT(*) as measurement_count,
    MAX(measurement_date) as latest_measurement,
    CASE 
        WHEN AVG(importance_score) > 0.8 THEN 'High'
        WHEN AVG(importance_score) > 0.5 THEN 'Medium'
        ELSE 'Low'
    END as importance_category
FROM feature_importance_tracking
WHERE measurement_date >= CURRENT_DATE - INTERVAL '1 month'
GROUP BY model_type, feature_name
ORDER BY model_type, avg_importance DESC;

-- View: Capacity Forecast Accuracy
CREATE OR REPLACE VIEW v_capacity_forecast_accuracy AS
SELECT 
    cf.model_used,
    cf.forecast_period_days,
    COUNT(*) as total_forecasts,
    AVG(cf.confidence_score) as avg_confidence,
    AVG(cf.predicted_utilization) as avg_predicted_utilization
FROM capacity_forecasts cf
WHERE cf.created_at >= CURRENT_DATE - INTERVAL '2 months'
GROUP BY cf.model_used, cf.forecast_period_days
ORDER BY cf.model_used, cf.forecast_period_days;

-- View: Active Scheduling Insights
CREATE OR REPLACE VIEW v_active_scheduling_insights AS
SELECT 
    insight_id,
    insight_type,
    scope_department,
    priority_level,
    jsonb_array_length(key_findings) as findings_count,
    jsonb_array_length(recommendations) as recommendations_count,
    created_at,
    expires_at
FROM scheduling_insights 
WHERE status = 'active' 
AND (expires_at IS NULL OR expires_at > NOW())
ORDER BY 
    CASE priority_level 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'normal' THEN 3 
        ELSE 4 
    END,
    created_at DESC;

-- Triggers for Automatic Data Management

-- Function to clean old training data
CREATE OR REPLACE FUNCTION cleanup_old_training_data()
RETURNS TRIGGER AS $$
BEGIN
    -- Keep only last 6 months of training data
    DELETE FROM ml_training_data 
    WHERE created_at < CURRENT_DATE - INTERVAL '6 months';
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to cleanup training data daily
DROP TRIGGER IF EXISTS trigger_cleanup_training_data ON ml_training_data;
CREATE TRIGGER trigger_cleanup_training_data
    AFTER INSERT ON ml_training_data
    EXECUTE FUNCTION cleanup_old_training_data();

-- Function to update model performance when feedback is received
CREATE OR REPLACE FUNCTION update_model_accuracy()
RETURNS TRIGGER AS $$
DECLARE
    avg_accuracy REAL;
    model_type_used VARCHAR(50);
BEGIN
    -- Get model type from prediction
    SELECT model_used INTO model_type_used 
    FROM prediction_results 
    WHERE prediction_id = NEW.prediction_id;
    
    -- Calculate new average accuracy for this model
    SELECT AVG(pf.feedback_score) INTO avg_accuracy
    FROM prediction_feedback pf
    JOIN prediction_results pr ON pf.prediction_id = pr.prediction_id
    WHERE pr.model_used = model_type_used
    AND pf.created_at >= CURRENT_DATE - INTERVAL '30 days';
    
    -- Update model performance if exists
    UPDATE ml_model_performance 
    SET accuracy = avg_accuracy
    WHERE model_type = model_type_used 
    AND is_active = TRUE;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update accuracy when feedback is added
DROP TRIGGER IF EXISTS trigger_update_model_accuracy ON prediction_feedback;
CREATE TRIGGER trigger_update_model_accuracy
    AFTER INSERT ON prediction_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_model_accuracy();

-- Function to expire old insights
CREATE OR REPLACE FUNCTION expire_old_insights()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-expire insights older than 30 days for normal priority
    -- Auto-expire insights older than 7 days for low priority
    UPDATE scheduling_insights 
    SET status = 'archived'
    WHERE status = 'active' 
    AND (
        (priority_level = 'normal' AND created_at < CURRENT_DATE - INTERVAL '30 days') OR
        (priority_level = 'low' AND created_at < CURRENT_DATE - INTERVAL '7 days')
    );
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to clean insights daily
DROP TRIGGER IF EXISTS trigger_expire_insights ON scheduling_insights;
CREATE TRIGGER trigger_expire_insights
    AFTER INSERT ON scheduling_insights
    EXECUTE FUNCTION expire_old_insights();

-- Insert sample data for development and testing

-- Sample ML training data
INSERT INTO ml_training_data (training_id, features, target_value, data_source, quality_score, metadata)
VALUES 
    ('train_001', '{"hour_of_day": 9, "day_of_week": 1, "dept_hash": 123, "priority": 0.8}', 9.5, 'historical_deliveries', 0.95, '{"report_type": "quality_daily"}'),
    ('train_002', '{"hour_of_day": 14, "day_of_week": 3, "dept_hash": 456, "priority": 0.5}', 14.2, 'historical_deliveries', 0.88, '{"report_type": "production_weekly"}'),
    ('train_003', '{"hour_of_day": 8, "day_of_week": 0, "dept_hash": 789, "priority": 1.0}', 8.1, 'historical_deliveries', 0.92, '{"report_type": "compliance_audit"}')
ON CONFLICT (training_id) DO NOTHING;

-- Sample model performance data
INSERT INTO ml_model_performance (model_id, model_type, model_version, accuracy, precision_score, recall_score, f1_score, mean_absolute_error, root_mean_square_error, training_samples, feature_importance)
VALUES 
    ('ensemble_v1_20241219', 'ensemble', 'v1.0', 0.87, 0.85, 0.82, 0.83, 0.8, 1.2, 1500, '{"hour_of_day": 0.3, "dept_hash": 0.25, "priority": 0.2, "day_of_week": 0.15}'),
    ('linear_v1_20241219', 'linear_regression', 'v1.0', 0.78, 0.75, 0.72, 0.73, 1.1, 1.8, 1200, '{"hour_of_day": 0.4, "priority": 0.3, "dept_hash": 0.2, "day_of_week": 0.1}'),
    ('timeseries_v1_20241219', 'time_series', 'v1.0', 0.82, 0.80, 0.79, 0.79, 0.9, 1.4, 1350, '{"seasonal": 0.5, "trend": 0.3, "hour_of_day": 0.2}')
ON CONFLICT (model_id) DO NOTHING;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ml_training_data TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON prediction_results TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON prediction_feedback TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ml_model_performance TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON pattern_analysis_results TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON capacity_forecasts TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON schedule_optimizations TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON feature_importance_tracking TO qms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON scheduling_insights TO qms_user;

-- Grant access to views
GRANT SELECT ON v_model_performance_summary TO qms_user;
GRANT SELECT ON v_prediction_accuracy_trends TO qms_user;
GRANT SELECT ON v_feature_importance_rankings TO qms_user;
GRANT SELECT ON v_capacity_forecast_accuracy TO qms_user;
GRANT SELECT ON v_active_scheduling_insights TO qms_user;

-- Grant sequence access
GRANT USAGE ON SEQUENCE ml_training_data_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE prediction_results_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE prediction_feedback_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE ml_model_performance_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE pattern_analysis_results_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE capacity_forecasts_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE schedule_optimizations_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE feature_importance_tracking_id_seq TO qms_user;
GRANT USAGE ON SEQUENCE scheduling_insights_id_seq TO qms_user;