import { apiClient } from './apiClient'
import { User, LoginCredentials, AuthResponse, PasswordChangeRequest } from '../types/auth-simple'

class AuthService {
  private readonly endpoints = {
    login: '/api/v1/auth/login',
    logout: '/api/v1/auth/logout',
    refresh: '/api/v1/auth/refresh',
    me: '/api/v1/auth/me',
    changePassword: '/api/v1/auth/change-password',
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
    const response = await apiClient.get<{ data: User }>(this.endpoints.me)
    return response.data.data
  }

  async changePassword(data: PasswordChangeRequest): Promise<void> {
    await apiClient.post(this.endpoints.changePassword, data)
  }

  hasPermission(user: User | null, permission: string): boolean {
    if (!user) return false
    if (user.roles?.includes('system_admin') || user.roles?.includes('admin')) {
      return true
    }
    return user.permissions?.includes(permission) || false
  }

  getUserRoles(user: User | null): string[] {
    return user?.roles || []
  }

  getUserDisplayName(user: User | null): string {
    if (!user) return 'Unknown User'
    return user.full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username
  }

  isSessionValid(): boolean {
    const token = localStorage.getItem('qms_token')
    if (!token) return false

    try {
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