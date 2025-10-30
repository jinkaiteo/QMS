// Organization Service - Phase A Sprint 2 Day 9
import apiClient from './apiClient'
import { ApiResponse } from '../types/common'
import {
  Department, 
  DepartmentNode, 
  Organization, 
  DepartmentRole,
  DepartmentAnalytics,
  OrganizationMetrics,
  CreateDepartmentRequest,
  UpdateDepartmentRequest,
  AssignRoleRequest,
  BulkRoleAssignmentRequest,
  DepartmentQueryParams,
  RoleAssignmentQueryParams
} from '../types/organization'

class OrganizationService {
  private baseURL = '/v1/organization'

  // Department Management
  async getDepartments(params?: DepartmentQueryParams): Promise<Department[]> {
    const response = await apiClient.get<ApiResponse<Department[]>>(`${this.baseURL}/departments`, { params })
    return response.data.data
  }

  async getDepartmentHierarchy(organizationId?: number): Promise<DepartmentNode[]> {
    const url = organizationId 
      ? `${this.baseURL}/departments/hierarchy?organization_id=${organizationId}`
      : `${this.baseURL}/departments/hierarchy`
    const response = await apiClient.get<ApiResponse<DepartmentNode[]>>(url)
    return response.data.data
  }

  async getDepartment(id: number): Promise<Department> {
    const response = await apiClient.get<ApiResponse<Department>>(`${this.baseURL}/departments/${id}`)
    return response.data.data
  }

  async createDepartment(data: CreateDepartmentRequest): Promise<Department> {
    const response = await apiClient.post<ApiResponse<Department>>(`${this.baseURL}/departments`, data)
    return response.data.data
  }

  async updateDepartment(id: number, data: UpdateDepartmentRequest): Promise<Department> {
    const response = await apiClient.put<ApiResponse<Department>>(`${this.baseURL}/departments/${id}`, data)
    return response.data.data
  }

  async deleteDepartment(id: number): Promise<void> {
    await apiClient.delete(`${this.baseURL}/departments/${id}`)
  }

  async moveDepartment(id: number, newParentId: number | null): Promise<Department> {
    const response = await apiClient.patch<ApiResponse<Department>>(
      `${this.baseURL}/departments/${id}/move`,
      { parent_department_id: newParentId }
    )
    return response.data.data
  }

  // Department Role Management
  async getDepartmentRoles(departmentId: number, params?: RoleAssignmentQueryParams): Promise<DepartmentRole[]> {
    const response = await apiClient.get<ApiResponse<DepartmentRole[]>>(
      `${this.baseURL}/departments/${departmentId}/roles`,
      { params }
    )
    return response.data.data
  }

  async assignRole(departmentId: number, data: AssignRoleRequest): Promise<DepartmentRole> {
    const response = await apiClient.post<ApiResponse<DepartmentRole>>(
      `${this.baseURL}/departments/${departmentId}/roles`,
      data
    )
    return response.data.data
  }

  async revokeRole(departmentId: number, roleId: number, userId: number): Promise<void> {
    await apiClient.delete(`${this.baseURL}/departments/${departmentId}/roles/${roleId}/users/${userId}`)
  }

  async bulkAssignRoles(data: BulkRoleAssignmentRequest): Promise<DepartmentRole[]> {
    const response = await apiClient.post<ApiResponse<DepartmentRole[]>>(
      `${this.baseURL}/departments/roles/bulk-assign`,
      data
    )
    return response.data.data
  }

  async getUserRoles(userId: number, departmentId?: number): Promise<DepartmentRole[]> {
    const params = departmentId ? { department_id: departmentId } : {}
    const response = await apiClient.get<ApiResponse<DepartmentRole[]>>(
      `${this.baseURL}/users/${userId}/roles`,
      { params }
    )
    return response.data.data
  }

  // Department Analytics
  async getDepartmentAnalytics(departmentId: number): Promise<DepartmentAnalytics> {
    const response = await apiClient.get<ApiResponse<DepartmentAnalytics>>(
      `${this.baseURL}/departments/${departmentId}/analytics`
    )
    return response.data.data
  }

  async getOrganizationMetrics(organizationId?: number): Promise<OrganizationMetrics> {
    const url = organizationId 
      ? `${this.baseURL}/metrics?organization_id=${organizationId}`
      : `${this.baseURL}/metrics`
    const response = await apiClient.get<ApiResponse<OrganizationMetrics>>(url)
    return response.data.data
  }

  async getDepartmentTrends(departmentId: number, period: string = '30d'): Promise<any> {
    const response = await apiClient.get<ApiResponse<any>>(
      `${this.baseURL}/departments/${departmentId}/trends?period=${period}`
    )
    return response.data.data
  }

  // Organization Management
  async getOrganizations(): Promise<Organization[]> {
    const response = await apiClient.get<ApiResponse<Organization[]>>(`${this.baseURL}/organizations`)
    return response.data.data
  }

  async getOrganization(id: number): Promise<Organization> {
    const response = await apiClient.get<ApiResponse<Organization>>(`${this.baseURL}/organizations/${id}`)
    return response.data.data
  }

  async createOrganization(data: Partial<Organization>): Promise<Organization> {
    const response = await apiClient.post<ApiResponse<Organization>>(`${this.baseURL}/organizations`, data)
    return response.data.data
  }

  async updateOrganization(id: number, data: Partial<Organization>): Promise<Organization> {
    const response = await apiClient.put<ApiResponse<Organization>>(`${this.baseURL}/organizations/${id}`, data)
    return response.data.data
  }

  async deleteOrganization(id: number): Promise<void> {
    await apiClient.delete(`${this.baseURL}/organizations/${id}`)
  }

  // Search and Filtering
  async searchDepartments(query: string, filters?: any): Promise<Department[]> {
    const response = await apiClient.get<ApiResponse<Department[]>>(
      `${this.baseURL}/departments/search`,
      { params: { q: query, ...filters } }
    )
    return response.data.data
  }

  async getDepartmentsByType(type: string): Promise<Department[]> {
    const response = await apiClient.get<ApiResponse<Department[]>>(
      `${this.baseURL}/departments`,
      { params: { department_type: [type] } }
    )
    return response.data.data
  }

  async getDepartmentsByParent(parentId: number): Promise<Department[]> {
    const response = await apiClient.get<ApiResponse<Department[]>>(
      `${this.baseURL}/departments`,
      { params: { parent_department_id: parentId } }
    )
    return response.data.data
  }

  // Validation
  async validateDepartmentCode(code: string, excludeId?: number): Promise<boolean> {
    const params = excludeId ? { exclude_id: excludeId } : {}
    const response = await apiClient.get<ApiResponse<{ is_available: boolean }>>(
      `${this.baseURL}/departments/validate-code/${code}`,
      { params }
    )
    return response.data.data.is_available
  }

  async validateHierarchy(departmentId: number, newParentId: number): Promise<boolean> {
    const response = await apiClient.get<ApiResponse<{ is_valid: boolean }>>(
      `${this.baseURL}/departments/${departmentId}/validate-parent/${newParentId}`
    )
    return response.data.data.is_valid
  }

  // Export functionality
  async exportDepartmentHierarchy(format: 'csv' | 'xlsx' | 'json' = 'xlsx'): Promise<Blob> {
    const response = await apiClient.get(
      `${this.baseURL}/departments/export?format=${format}`,
      { responseType: 'blob' }
    )
    return response.data
  }

  async exportRoleAssignments(departmentId?: number, format: 'csv' | 'xlsx' = 'xlsx'): Promise<Blob> {
    const params = departmentId ? { department_id: departmentId } : {}
    const response = await apiClient.get(
      `${this.baseURL}/roles/export?format=${format}`,
      { params, responseType: 'blob' }
    )
    return response.data
  }
}

export const organizationService = new OrganizationService()
export default organizationService