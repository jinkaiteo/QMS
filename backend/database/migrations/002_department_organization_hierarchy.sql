-- Phase A Sprint 2: Department & Organization Hierarchy Database Migration
-- Migration: 002_department_organization_hierarchy.sql
-- Date: 2025-10-27
-- Description: Add hierarchical department structure and enhanced organization management

-- Enhance existing departments table with hierarchy support
ALTER TABLE departments ADD COLUMN IF NOT EXISTS parent_department_id INTEGER;
ALTER TABLE departments ADD COLUMN IF NOT EXISTS department_code VARCHAR(20);
ALTER TABLE departments ADD COLUMN IF NOT EXISTS department_head_id INTEGER;
ALTER TABLE departments ADD COLUMN IF NOT EXISTS cost_center VARCHAR(50);
ALTER TABLE departments ADD COLUMN IF NOT EXISTS location VARCHAR(100);
ALTER TABLE departments ADD COLUMN IF NOT EXISTS department_type VARCHAR(50);
ALTER TABLE departments ADD COLUMN IF NOT EXISTS hierarchy_path TEXT;
ALTER TABLE departments ADD COLUMN IF NOT EXISTS hierarchy_level INTEGER DEFAULT 0;

-- Add foreign key constraints for departments
ALTER TABLE departments ADD CONSTRAINT fk_departments_parent 
    FOREIGN KEY (parent_department_id) REFERENCES departments(id);

ALTER TABLE departments ADD CONSTRAINT fk_departments_head 
    FOREIGN KEY (department_head_id) REFERENCES users(id);

-- Add unique constraint for department code
ALTER TABLE departments ADD CONSTRAINT uk_departments_code UNIQUE (department_code);

-- Enhance existing organizations table
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS organization_type VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS parent_organization_id INTEGER;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS regulatory_region VARCHAR(50);

-- Add foreign key constraint for organization hierarchy
ALTER TABLE organizations ADD CONSTRAINT fk_organizations_parent 
    FOREIGN KEY (parent_organization_id) REFERENCES organizations(id);

-- Create department roles bridge table for department-specific role assignments
CREATE TABLE IF NOT EXISTS department_roles (
    id SERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by INTEGER,
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_department_roles_department 
        FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    CONSTRAINT fk_department_roles_role 
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_department_roles_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_department_roles_assigned_by 
        FOREIGN KEY (assigned_by) REFERENCES users(id),
    CONSTRAINT uk_department_roles_unique 
        UNIQUE(department_id, role_id, user_id)
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_departments_parent ON departments(parent_department_id);
CREATE INDEX IF NOT EXISTS idx_departments_head ON departments(department_head_id);
CREATE INDEX IF NOT EXISTS idx_departments_hierarchy_path ON departments USING GIN (to_tsvector('simple', hierarchy_path));
CREATE INDEX IF NOT EXISTS idx_departments_hierarchy_level ON departments(hierarchy_level);
CREATE INDEX IF NOT EXISTS idx_departments_type ON departments(department_type);
CREATE INDEX IF NOT EXISTS idx_departments_organization ON departments(organization_id);

CREATE INDEX IF NOT EXISTS idx_organizations_parent ON organizations(parent_organization_id);
CREATE INDEX IF NOT EXISTS idx_organizations_type ON organizations(organization_type);

CREATE INDEX IF NOT EXISTS idx_department_roles_department ON department_roles(department_id);
CREATE INDEX IF NOT EXISTS idx_department_roles_user ON department_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_department_roles_role ON department_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_department_roles_active ON department_roles(is_active, valid_from, valid_until);

-- Create function to update hierarchy path automatically
CREATE OR REPLACE FUNCTION update_department_hierarchy_path()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate hierarchy level and path
    IF NEW.parent_department_id IS NULL THEN
        NEW.hierarchy_level = 0;
        NEW.hierarchy_path = '';
    ELSE
        SELECT 
            hierarchy_level + 1,
            CASE 
                WHEN hierarchy_path = '' THEN parent_department_id::text
                ELSE hierarchy_path || '.' || parent_department_id::text
            END
        INTO NEW.hierarchy_level, NEW.hierarchy_path
        FROM departments 
        WHERE id = NEW.parent_department_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update hierarchy path
DROP TRIGGER IF EXISTS trigger_update_department_hierarchy ON departments;
CREATE TRIGGER trigger_update_department_hierarchy
    BEFORE INSERT OR UPDATE OF parent_department_id ON departments
    FOR EACH ROW
    EXECUTE FUNCTION update_department_hierarchy_path();

-- Function to get all department descendants
CREATE OR REPLACE FUNCTION get_department_descendants(dept_id INTEGER)
RETURNS TABLE(id INTEGER, name VARCHAR, hierarchy_level INTEGER, hierarchy_path TEXT) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE dept_tree AS (
        -- Base case: the department itself
        SELECT d.id, d.name, d.hierarchy_level, d.hierarchy_path
        FROM departments d
        WHERE d.id = dept_id
        
        UNION ALL
        
        -- Recursive case: children of current departments
        SELECT d.id, d.name, d.hierarchy_level, d.hierarchy_path
        FROM departments d
        INNER JOIN dept_tree dt ON d.parent_department_id = dt.id
    )
    SELECT dt.id, dt.name, dt.hierarchy_level, dt.hierarchy_path
    FROM dept_tree dt
    WHERE dt.id != dept_id;  -- Exclude the root department itself
END;
$$ LANGUAGE plpgsql;

-- Function to get all department ancestors
CREATE OR REPLACE FUNCTION get_department_ancestors(dept_id INTEGER)
RETURNS TABLE(id INTEGER, name VARCHAR, hierarchy_level INTEGER, hierarchy_path TEXT) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE dept_tree AS (
        -- Base case: the department itself
        SELECT d.id, d.name, d.hierarchy_level, d.hierarchy_path, d.parent_department_id
        FROM departments d
        WHERE d.id = dept_id
        
        UNION ALL
        
        -- Recursive case: parents of current departments
        SELECT d.id, d.name, d.hierarchy_level, d.hierarchy_path, d.parent_department_id
        FROM departments d
        INNER JOIN dept_tree dt ON d.id = dt.parent_department_id
    )
    SELECT dt.id, dt.name, dt.hierarchy_level, dt.hierarchy_path
    FROM dept_tree dt
    WHERE dt.id != dept_id;  -- Exclude the starting department itself
END;
$$ LANGUAGE plpgsql;

-- Insert default department types if they don't exist
INSERT INTO departments (organization_id, name, code, description, department_type, hierarchy_level, hierarchy_path)
SELECT 1, 'Corporate', 'CORP', 'Corporate Headquarters', 'administrative', 0, ''
WHERE NOT EXISTS (SELECT 1 FROM departments WHERE code = 'CORP') AND EXISTS (SELECT 1 FROM organizations LIMIT 1);

INSERT INTO departments (organization_id, name, code, description, department_type, hierarchy_level, hierarchy_path, parent_department_id)
SELECT 1, 'Quality Assurance', 'QA', 'Quality Assurance Department', 'quality', 1, '1', 
    (SELECT id FROM departments WHERE code = 'CORP')
WHERE NOT EXISTS (SELECT 1 FROM departments WHERE code = 'QA') 
    AND EXISTS (SELECT 1 FROM departments WHERE code = 'CORP');

INSERT INTO departments (organization_id, name, code, description, department_type, hierarchy_level, hierarchy_path, parent_department_id)
SELECT 1, 'Manufacturing', 'MFG', 'Manufacturing Operations', 'operational', 1, '1',
    (SELECT id FROM departments WHERE code = 'CORP')
WHERE NOT EXISTS (SELECT 1 FROM departments WHERE code = 'MFG') 
    AND EXISTS (SELECT 1 FROM departments WHERE code = 'CORP');

-- Update existing departments with default hierarchy information
UPDATE departments 
SET hierarchy_level = 0, hierarchy_path = ''
WHERE parent_department_id IS NULL AND hierarchy_level IS NULL;

UPDATE departments 
SET department_type = 'operational'
WHERE department_type IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN departments.parent_department_id IS 'Parent department for hierarchy structure';
COMMENT ON COLUMN departments.department_code IS 'Unique department code identifier';
COMMENT ON COLUMN departments.department_head_id IS 'Department head/manager user ID';
COMMENT ON COLUMN departments.cost_center IS 'Financial cost center code';
COMMENT ON COLUMN departments.location IS 'Physical location of department';
COMMENT ON COLUMN departments.department_type IS 'Type: operational, administrative, quality';
COMMENT ON COLUMN departments.hierarchy_path IS 'Materialized path for efficient hierarchy queries';
COMMENT ON COLUMN departments.hierarchy_level IS 'Depth level in hierarchy (0 = root)';

COMMENT ON COLUMN organizations.organization_type IS 'Type: manufacturing, laboratory, corporate';
COMMENT ON COLUMN organizations.parent_organization_id IS 'Parent organization for multi-org hierarchy';
COMMENT ON COLUMN organizations.regulatory_region IS 'Regulatory region: FDA, EMA, PMDA, etc.';

COMMENT ON TABLE department_roles IS 'Department-specific role assignments for users';
COMMENT ON COLUMN department_roles.valid_from IS 'Role assignment start date';
COMMENT ON COLUMN department_roles.valid_until IS 'Role assignment end date (optional)';
COMMENT ON COLUMN department_roles.assigned_by IS 'User who assigned the role';

-- Create view for easy hierarchy navigation
CREATE OR REPLACE VIEW department_hierarchy_view AS
SELECT 
    d.id,
    d.name,
    d.code,
    d.description,
    d.department_type,
    d.location,
    d.cost_center,
    d.hierarchy_level,
    d.hierarchy_path,
    d.organization_id,
    d.parent_department_id,
    pd.name as parent_department_name,
    d.department_head_id,
    CONCAT(u.first_name, ' ', u.last_name) as department_head_name,
    u.job_title as department_head_title,
    (SELECT COUNT(*) FROM users WHERE department_id = d.id AND is_deleted = FALSE) as direct_user_count,
    (SELECT COUNT(*) FROM departments WHERE parent_department_id = d.id) as child_department_count,
    o.name as organization_name
FROM departments d
LEFT JOIN departments pd ON d.parent_department_id = pd.id
LEFT JOIN users u ON d.department_head_id = u.id
LEFT JOIN organizations o ON d.organization_id = o.id
WHERE d.is_active = TRUE;

COMMENT ON VIEW department_hierarchy_view IS 'Comprehensive view of department hierarchy with related information';