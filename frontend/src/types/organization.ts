// Organization Management Types - Phase A Sprint 2 Day 9

export interface Department {
  id: number
  uuid: string
  name: string
  description?: string
  department_code?: string
  code?: string // Alias for department_code
  cost_center?: string
  location?: string
  department_type: 'operational' | 'administrative' | 'quality'
  parent_department_id?: number
  hierarchy_path?: string
  hierarchy_level: number
  is_active: boolean
  created_at: string
  updated_at: string
  
  // Relationships
  parent_department?: Department
  child_departments?: Department[]
  department_head?: {
    id: number
    full_name: string
    job_title?: string
    profile_picture_url?: string
  }
  user_count?: number
  
  // Computed properties
  full_hierarchy_name?: string
  effective_permissions?: string[]
}

export interface DepartmentNode extends Department {
  children: DepartmentNode[]
  expanded?: boolean
  selected?: boolean
}

export interface Organization {
  id: number
  uuid: string
  name: string
  description?: string
  organization_type: 'manufacturing' | 'laboratory' | 'corporate'
  parent_organization_id?: number
  regulatory_region: 'FDA' | 'EMA' | 'PMDA' | 'ICH'
  is_active: boolean
  created_at: string
  updated_at: string
  
  // Relationships
  parent_organization?: Organization
  child_organizations?: Organization[]
  departments?: Department[]
}

export interface DepartmentRole {
  id: number
  department_id: number
  role_id: number
  user_id: number
  assigned_by?: number
  valid_from: string
  valid_until?: string
  is_active: boolean
  created_at: string
  updated_at: string
  
  // Relationships
  department: Department
  role: {
    id: number
    name: string
    display_name: string
    permissions: string[]
  }
  user: {
    id: number
    full_name: string
    job_title?: string
    avatar_url?: string
  }
  assigned_by_user?: {
    id: number
    full_name: string
  }
}

export interface DepartmentRoleAssignment {
  department_id: number
  role_id: number
  user_id: number
  valid_from?: string
  valid_until?: string
}

export interface DepartmentAnalytics {
  department_id: number
  department_name: string
  total_users: number
  active_users: number
  role_distribution: {
    role_name: string
    user_count: number
  }[]
  permission_coverage: {
    permission: string
    user_count: number
  }[]
  hierarchy_depth: number
  child_department_count: number
  compliance_score: number
  last_activity: string
}

export interface OrganizationMetrics {
  total_departments: number
  total_users: number
  active_departments: number
  hierarchy_levels: number
  role_assignments: number
  permission_violations: number
  compliance_status: 'compliant' | 'non_compliant' | 'warning'
  last_audit: string
}

// Request/Response types
export interface CreateDepartmentRequest {
  name: string
  description?: string
  department_code?: string
  cost_center?: string
  location?: string
  department_type: 'operational' | 'administrative' | 'quality'
  parent_department_id?: number
  department_head_id?: number
}

export interface UpdateDepartmentRequest {
  name?: string
  description?: string
  department_code?: string
  cost_center?: string
  location?: string
  department_type?: 'operational' | 'administrative' | 'quality'
  parent_department_id?: number
  department_head_id?: number
  is_active?: boolean
}

export interface AssignRoleRequest {
  user_id: number
  role_id: number
  valid_from?: string
  valid_until?: string
}

export interface BulkRoleAssignmentRequest {
  assignments: {
    user_id: number
    role_id: number
    department_id: number
    valid_from?: string
    valid_until?: string
  }[]
}

// Filter and query types
export interface DepartmentQueryParams {
  department_type?: string[]
  hierarchy_level?: number
  parent_department_id?: number
  include_inactive?: boolean
  include_children?: boolean
  include_analytics?: boolean
  search?: string
  page?: number
  limit?: number
}

export interface RoleAssignmentQueryParams {
  department_id?: number
  user_id?: number
  role_id?: number
  include_expired?: boolean
  valid_on?: string
  page?: number
  limit?: number
}