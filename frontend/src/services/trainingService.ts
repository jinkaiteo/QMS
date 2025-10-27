import { apiClient } from './apiClient'
import { authService } from './authService'

export interface TrainingProgram {
  id: string
  title: string
  description: string
  type: 'mandatory' | 'compliance' | 'safety' | 'technical' | 'leadership'
  duration: number // in hours
  passingScore: number
  validityPeriod: number // in months
  status: 'active' | 'draft' | 'archived'
  createdBy: string
  createdAt: string
  updatedAt: string
  modules: TrainingModule[]
  linkedDocuments: LinkedDocument[]
}

export interface TrainingModule {
  id: string
  title: string
  description: string
  content: string
  duration: number // in minutes
  order: number
}

export interface LinkedDocument {
  id: string
  title: string
  type: 'SOP' | 'Form' | 'Policy' | 'Manual' | 'Certificate'
  category: 'Reference Material' | 'Training Form' | 'Certificate Template'
}

export interface TrainingAssignment {
  id: string
  programId: string
  employeeId: string
  assignedBy: string
  assignedAt: string
  dueDate: string
  status: 'assigned' | 'in_progress' | 'completed' | 'overdue'
  progress: number
  completedAt?: string
  score?: number
}

export interface CreateProgramRequest {
  title: string
  description: string
  type: string
  duration: number
  passingScore: number
  validityPeriod: number
  linkedDocuments: string[]
  modules: Omit<TrainingModule, 'id'>[]
}

export interface AssignTrainingRequest {
  programId: string
  employeeIds: string[]
  dueDate: string
  notes?: string
  notifyEmployees: boolean
  notifyManagers: boolean
}

class TrainingService {
  private readonly baseUrl = '/v1/training'

  // Training Programs
  async getPrograms(): Promise<TrainingProgram[]> {
    const response = await apiClient.get(`${this.baseUrl}/programs`)
    return response.data
  }

  async getProgram(id: string): Promise<TrainingProgram> {
    const response = await apiClient.get(`${this.baseUrl}/programs/${id}`)
    return response.data
  }

  async createProgram(program: CreateProgramRequest): Promise<TrainingProgram> {
    const response = await apiClient.post(`${this.baseUrl}/programs`, program)
    return response.data
  }

  async updateProgram(id: string, program: Partial<CreateProgramRequest>): Promise<TrainingProgram> {
    const response = await apiClient.put(`${this.baseUrl}/programs/${id}`, program)
    return response.data
  }

  async deleteProgram(id: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/programs/${id}`)
  }

  // Training Assignments
  async getMyAssignments(): Promise<TrainingAssignment[]> {
    const response = await apiClient.get(`${this.baseUrl}/my-training`)
    return response.data
  }

  async getAssignments(employeeId?: string): Promise<TrainingAssignment[]> {
    const url = employeeId 
      ? `${this.baseUrl}/assignments?employee_id=${employeeId}`
      : `${this.baseUrl}/assignments`
    const response = await apiClient.get(url)
    return response.data
  }

  async assignTraining(assignment: AssignTrainingRequest): Promise<TrainingAssignment[]> {
    const response = await apiClient.post(`${this.baseUrl}/assignments`, assignment)
    return response.data
  }

  async updateAssignmentProgress(id: string, progress: number): Promise<TrainingAssignment> {
    const response = await apiClient.patch(`${this.baseUrl}/assignments/${id}/progress`, { progress })
    return response.data
  }

  async completeTraining(id: string, score: number, signature: string): Promise<TrainingAssignment> {
    const response = await apiClient.post(`${this.baseUrl}/assignments/${id}/complete`, {
      score,
      signature,
      completedAt: new Date().toISOString()
    })
    return response.data
  }

  // Training Records
  async getTrainingRecords(employeeId?: string): Promise<TrainingAssignment[]> {
    const url = employeeId 
      ? `${this.baseUrl}/records?employee_id=${employeeId}`
      : `${this.baseUrl}/records/my`
    const response = await apiClient.get(url)
    return response.data
  }

  // Dashboard Statistics
  async getDashboardStats(): Promise<{
    totalPrograms: number
    activeAssignments: number
    completedThisMonth: number
    overdueTrainings: number
    complianceRate: number
  }> {
    const response = await apiClient.get(`${this.baseUrl}/dashboard`)
    return response.data
  }

  // Employee List for Assignments
  async getEmployees(): Promise<Array<{
    id: string
    name: string
    email: string
    department: string
    jobRole: string
  }>> {
    const response = await apiClient.get('/v1/users/employees')
    return response.data
  }

  // Error Handling Helper
  handleError(error: any): string {
    if (error.response?.data?.message) {
      return error.response.data.message
    }
    if (error.message) {
      return error.message
    }
    return 'An unexpected error occurred'
  }
}

export const trainingService = new TrainingService()