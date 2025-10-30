import { apiClient } from './apiClient'
import { User, LoginCredentials, AuthResponse, PasswordChangeRequest } from '@types/auth'
import { ApiResponse } from '@types/common'

class AuthService {
  private readonly endpoints = {
    login: '/v1/auth/login',
    logout: '/v1/auth/logout',
    refresh: '/v1/auth/refresh',
    me: '/v1/auth/me',
    changePassword: '/v1/auth/change-password',
    resetPassword: '/v1/auth/reset-password',
    verifyToken: '/v1/auth/verify-token',
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      this.endpoints.login,
      credentials
    )
    return response.data
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post(this.endpoints.logout)
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API call failed:', error)
    }
  }

  async refreshToken(): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      this.endpoints.refresh
    )
    return response.data
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<ApiResponse<User>>(this.endpoints.me)
    return response.data.data
  }

  async changePassword(data: PasswordChangeRequest): Promise<void> {
    await apiClient.post<ApiResponse<void>>(this.endpoints.changePassword, data)
  }

  async resetPassword(email: string): Promise<void> {
    await apiClient.post<ApiResponse<void>>(this.endpoints.resetPassword, { email })
  }

  async verifyToken(): Promise<boolean> {
    try {
      await apiClient.get(this.endpoints.verifyToken)
      return true
    } catch (error) {
      return false
    }
  }

  // Check if user has specific permission
  hasPermission(user: User | null, permission: string): boolean {
    if (!user) return false
    return user.permissions.includes(permission) || user.role === 'admin'
  }

  // Check if user has any of the specified roles
  hasRole(user: User | null, roles: string[]): boolean {
    if (!user) return false
    return roles.includes(user.role) || user.role === 'admin'
  }

  // Get user's display name
  getUserDisplayName(user: User | null): string {
    if (!user) return 'Unknown User'
    return user.full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username
  }

  // Check if user has specific permission (simplified for demo)
  checkPermission(user: User | null, permission: string): boolean {
    if (!user) return false
    
    // For demo purposes, admin users have all permissions
    if (user.roles?.includes('system_admin') || user.roles?.includes('admin')) {
      return true
    }
    
    // Check user's permissions array
    return user.permissions?.includes(permission) || false
  }

  // Get user roles
  getUserRoles(user: User | null): string[] {
    return user?.roles || []
  }

  // Check if user's session is still valid
  isSessionValid(): boolean {
    const token = localStorage.getItem('qms_token')
    if (!token) return false

    try {
      // Simple JWT expiration check (in a real app, you might want to decode the JWT)
      const tokenData = JSON.parse(atob(token.split('.')[1]))
      const now = Date.now() / 1000
      return tokenData.exp > now
    } catch (error) {
      return false
    }
  }
}

export const authService = new AuthService()
export default authService