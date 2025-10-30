// Simplified auth types for production deployment
export interface User {
  id: number
  username: string
  email: string
  first_name?: string
  last_name?: string
  full_name?: string
  roles?: string[]
  permissions?: string[]
  status?: string
  last_login?: string
  created_at?: string
  updated_at?: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  user: User
}

export interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
  confirm_password: string
}