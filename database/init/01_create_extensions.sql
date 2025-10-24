-- QMS Database Initialization Script
-- Phase 1: Create required PostgreSQL extensions and base configuration

-- Enable required extensions for QMS functionality
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";        -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";         -- Cryptographic functions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";          -- Trigram matching for search
CREATE EXTENSION IF NOT EXISTS "btree_gin";        -- GIN indexes for better performance
CREATE EXTENSION IF NOT EXISTS "unaccent";         -- Remove accents for search

-- Create custom types for the application
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'locked', 'pending');
CREATE TYPE document_status AS ENUM ('draft', 'pending_review', 'reviewed', 'pending_approval', 'approved', 'rejected', 'obsolete', 'superseded');
CREATE TYPE workflow_state AS ENUM ('pending', 'in_progress', 'completed', 'cancelled', 'rejected');
CREATE TYPE audit_action AS ENUM ('CREATE', 'READ', 'UPDATE', 'DELETE', 'INSERT', 'LOGIN', 'LOGOUT', 'APPROVE', 'REJECT');
CREATE TYPE signature_type AS ENUM ('author', 'reviewer', 'approver', 'witness');

-- Set default timezone to UTC for compliance
SET timezone = 'UTC';

-- Create audit logging function for 21 CFR Part 11 compliance
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS trigger AS $$
DECLARE
    old_data jsonb;
    new_data jsonb;
    current_user_id integer;
BEGIN
    -- Get current user ID from application context
    current_user_id := current_setting('app.current_user_id', true)::integer;
    
    -- Handle different trigger operations
    IF TG_OP = 'DELETE' THEN
        old_data := to_jsonb(OLD);
        INSERT INTO audit_logs (
            table_name, record_id, action, old_values, 
            user_id, timestamp, ip_address
        ) VALUES (
            TG_TABLE_NAME, OLD.id, 'DELETE', old_data,
            current_user_id, CURRENT_TIMESTAMP AT TIME ZONE 'UTC',
            current_setting('app.client_ip', true)
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);
        INSERT INTO audit_logs (
            table_name, record_id, action, old_values, new_values,
            user_id, timestamp, ip_address
        ) VALUES (
            TG_TABLE_NAME, NEW.id, 'UPDATE', old_data, new_data,
            current_user_id, CURRENT_TIMESTAMP AT TIME ZONE 'UTC',
            current_setting('app.client_ip', true)
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        new_data := to_jsonb(NEW);
        INSERT INTO audit_logs (
            table_name, record_id, action, new_values,
            user_id, timestamp, ip_address
        ) VALUES (
            TG_TABLE_NAME, NEW.id, 'INSERT', new_data,
            current_user_id, CURRENT_TIMESTAMP AT TIME ZONE 'UTC',
            current_setting('app.client_ip', true)
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create function to update timestamps automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP AT TIME ZONE 'UTC';
    NEW.version = COALESCE(OLD.version, 0) + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create function for data hash calculation (data integrity)
CREATE OR REPLACE FUNCTION calculate_data_hash(data_row jsonb)
RETURNS text AS $$
BEGIN
    RETURN encode(digest(data_row::text, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Create sequence for audit log IDs to ensure proper ordering
CREATE SEQUENCE IF NOT EXISTS audit_log_seq START 1;

COMMENT ON EXTENSION "uuid-ossp" IS 'UUID generation for unique record identification';
COMMENT ON EXTENSION "pgcrypto" IS 'Cryptographic functions for data integrity and security';
COMMENT ON EXTENSION "pg_trgm" IS 'Trigram matching for full-text search capabilities';

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO qms_user;
GRANT CREATE ON SCHEMA public TO qms_user;