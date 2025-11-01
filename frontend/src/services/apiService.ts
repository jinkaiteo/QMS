import axios, { AxiosResponse } from 'axios'

// API Base URL
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || '/api/v1'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('qms_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('qms_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Generic API service class
export class ApiService {
  // Generic GET request
  static async get<T>(endpoint: string): Promise<T> {
    try {
      const response: AxiosResponse<T> = await apiClient.get(endpoint)
      return response.data
    } catch (error) {
      console.error(`API GET Error for ${endpoint}:`, error)
      throw error
    }
  }

  // Generic POST request
  static async post<T>(endpoint: string, data: any): Promise<T> {
    try {
      const response: AxiosResponse<T> = await apiClient.post(endpoint, data)
      return response.data
    } catch (error) {
      console.error(`API POST Error for ${endpoint}:`, error)
      throw error
    }
  }

  // Generic PUT request
  static async put<T>(endpoint: string, data: any): Promise<T> {
    try {
      const response: AxiosResponse<T> = await apiClient.put(endpoint, data)
      return response.data
    } catch (error) {
      console.error(`API PUT Error for ${endpoint}:`, error)
      throw error
    }
  }

  // Generic DELETE request
  static async delete<T>(endpoint: string): Promise<T> {
    try {
      const response: AxiosResponse<T> = await apiClient.delete(endpoint)
      return response.data
    } catch (error) {
      console.error(`API DELETE Error for ${endpoint}:`, error)
      throw error
    }
  }

  // File upload with progress tracking
  static async uploadFile(
    endpoint: string, 
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<any> {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiClient.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        },
      })

      return response.data
    } catch (error) {
      console.error(`File Upload Error for ${endpoint}:`, error)
      throw error
    }
  }

  // Download file
  static async downloadFile(endpoint: string, filename: string): Promise<void> {
    try {
      const response = await apiClient.get(endpoint, {
        responseType: 'blob',
      })

      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error(`Download Error for ${endpoint}:`, error)
      throw error
    }
  }
}

// Document API Service
export class DocumentService extends ApiService {
  static async getDocuments(): Promise<any[]> {
    return this.get('/documents')
  }

  static async getDocument(id: string): Promise<any> {
    return this.get(`/documents/${id}`)
  }

  static async createDocument(documentData: any): Promise<any> {
    return this.post('/documents', documentData)
  }

  static async updateDocument(id: string, documentData: any): Promise<any> {
    return this.put(`/documents/${id}`, documentData)
  }

  static async deleteDocument(id: string): Promise<any> {
    return this.delete(`/documents/${id}`)
  }

  static async uploadDocument(file: File, metadata: any, onProgress?: (progress: number) => void): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('metadata', JSON.stringify(metadata))

    return apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    }).then(response => response.data)
  }

  static async downloadDocument(id: string, filename: string): Promise<void> {
    return this.downloadFile(`/documents/${id}/download`, filename)
  }
}

// Training API Service
export class TrainingService extends ApiService {
  static async getPrograms(): Promise<any[]> {
    return this.get('/training/programs')
  }

  static async createProgram(programData: any): Promise<any> {
    return this.post('/training/programs', programData)
  }

  static async getAssignments(): Promise<any[]> {
    return this.get('/training/assignments')
  }

  static async createAssignment(assignmentData: any): Promise<any> {
    return this.post('/training/assignments', assignmentData)
  }

  static async updateAssignmentProgress(id: string, progress: number): Promise<any> {
    return this.put(`/training/assignments/${id}/progress`, { progress })
  }
}

// Quality API Service
export class QualityService extends ApiService {
  static async getQualityEvents(): Promise<any[]> {
    return this.get('/quality/events')
  }

  static async createQualityEvent(eventData: any): Promise<any> {
    return this.post('/quality/events', eventData)
  }

  static async getCAPAs(): Promise<any[]> {
    return this.get('/quality/capas')
  }

  static async createCAPA(capaData: any): Promise<any> {
    return this.post('/quality/capas', capaData)
  }

  static async updateCAPAProgress(id: string, progress: number): Promise<any> {
    return this.put(`/quality/capas/${id}/progress`, { progress })
  }
}

// LIMS API Service
export class LIMSService extends ApiService {
  static async getSamples(): Promise<any[]> {
    return this.get('/lims/samples')
  }

  static async createSample(sampleData: any): Promise<any> {
    return this.post('/lims/samples', sampleData)
  }

  static async getTestMethods(): Promise<any[]> {
    return this.get('/lims/test-methods')
  }

  static async getTestResults(): Promise<any[]> {
    return this.get('/lims/test-results')
  }

  static async createTestResult(resultData: any): Promise<any> {
    return this.post('/lims/test-results', resultData)
  }
}

// Analytics API Service
export class AnalyticsService extends ApiService {
  static async getDashboardStats(): Promise<any> {
    return this.get('/analytics/dashboard')
  }

  static async getModuleStats(module: string): Promise<any> {
    return this.get(`/analytics/modules/${module}`)
  }

  static async getComplianceReport(): Promise<any> {
    return this.get('/analytics/compliance')
  }

  static async exportReport(reportType: string, format: 'pdf' | 'excel'): Promise<void> {
    return this.downloadFile(`/analytics/reports/${reportType}/export?format=${format}`, `${reportType}_report.${format}`)
  }
}

// Notification Service
export class NotificationService extends ApiService {
  static async getNotifications(): Promise<any[]> {
    return this.get('/notifications')
  }

  static async markAsRead(id: string): Promise<any> {
    return this.put(`/notifications/${id}/read`, {})
  }

  static async sendNotification(notificationData: any): Promise<any> {
    return this.post('/notifications/send', notificationData)
  }
}

export default ApiService