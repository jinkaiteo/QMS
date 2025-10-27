// Authentication related types for QMS Platform v3.0

export interface User {
  id: number
  username: string
  email: string
  full_name: string
  first_name?: string  // Optional for backward compatibility
  last_name?: string   // Optional for backward compatibility
  roles: string[]      // Backend returns array of role names
  department?: string
  organization?: string
  status: string
  is_active?: boolean
  last_login?: string
  created_at?: string
  updated_at?: string
  permissions?: string[]
  profile?: {
    phone?: string
    position?: string
    supervisor?: string
    employee_id?: string
  }
}

export interface LoginCredentials {
  username: string
  password: string
  remember_me?: boolean
}

export interface AuthResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
  user: User
  permissions: string[]
}

export interface TokenRefreshRequest {
  refresh_token: string
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordResetConfirm {
  token: string
  new_password: string
  confirm_password: string
}

// Role-based permissions
export interface Permission {
  id: string
  name: string
  codename: string
  content_type: string
  description?: string
}

export interface Role {
  id: string
  name: string
  description?: string
  permissions: Permission[]
  is_active: boolean
}

// Session management
export interface Session {
  id: string
  user_id: string
  token: string
  created_at: string
  expires_at: string
  is_active: boolean
  ip_address?: string
  user_agent?: string
  last_activity: string
}

// Audit trail for authentication
export interface AuthAuditLog {
  id: string
  user_id?: string
  action: 'login' | 'logout' | 'login_failed' | 'password_change' | 'token_refresh'
  ip_address: string
  user_agent: string
  timestamp: string
  details?: Record<string, any>
  success: boolean
}