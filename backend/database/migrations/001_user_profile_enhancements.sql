-- Phase A Sprint 1: User Profile Enhancement Database Migration
-- Migration: 001_user_profile_enhancements.sql
-- Date: 2025-10-27
-- Description: Add enhanced user profile capabilities

-- Add profile fields to existing users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture_url VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS hire_date DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS employee_id VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS supervisor_id INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0;

-- Add foreign key constraint for supervisor
ALTER TABLE users ADD CONSTRAINT fk_users_supervisor 
    FOREIGN KEY (supervisor_id) REFERENCES users(id);

-- Add unique constraint for employee_id
ALTER TABLE users ADD CONSTRAINT uk_users_employee_id UNIQUE (employee_id);

-- Create user preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT fk_user_preferences_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uk_user_preferences_user_key 
        UNIQUE(user_id, preference_key)
);

-- Create user sessions table for activity tracking
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_user_sessions_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(preference_key);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active, last_activity_at);
CREATE INDEX IF NOT EXISTS idx_users_supervisor ON users(supervisor_id);
CREATE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id);

-- Insert default preferences for existing users
INSERT INTO user_preferences (user_id, preference_key, preference_value)
SELECT id, 'theme', 'light' FROM users 
WHERE id NOT IN (SELECT user_id FROM user_preferences WHERE preference_key = 'theme');

INSERT INTO user_preferences (user_id, preference_key, preference_value)
SELECT id, 'language', 'en' FROM users 
WHERE id NOT IN (SELECT user_id FROM user_preferences WHERE preference_key = 'language');

INSERT INTO user_preferences (user_id, preference_key, preference_value)
SELECT id, 'timezone', 'UTC' FROM users 
WHERE id NOT IN (SELECT user_id FROM user_preferences WHERE preference_key = 'timezone');

-- Add comments for documentation
COMMENT ON TABLE user_preferences IS 'User-specific preferences and settings';
COMMENT ON TABLE user_sessions IS 'User login sessions for activity tracking';
COMMENT ON COLUMN users.profile_picture_url IS 'URL to user profile picture';
COMMENT ON COLUMN users.supervisor_id IS 'ID of user supervisor for hierarchy';
COMMENT ON COLUMN users.employee_id IS 'Unique employee identifier';
COMMENT ON COLUMN users.last_login_at IS 'Timestamp of last successful login';
COMMENT ON COLUMN users.login_count IS 'Total number of successful logins';