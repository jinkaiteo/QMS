import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { store } from '@store/store'
import { clearCredentials, refreshAccessToken } from '@store/slices/authSlice'

// API client configuration for QMS Platform v3.0
class ApiClient {
  private instance: AxiosInstance
  private isRefreshing = false
  private failedQueue: Array<{
    resolve: (token: string) => void
    reject: (error: any) => void
  }> = []

  constructor() {
    this.instance = axios.create({
      baseURL: (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      withCredentials: false,
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor - Add auth token
    this.instance.interceptors.request.use(
      (config) => {
        const state = store.getState()
        const token = state.auth.token

        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Add correlation ID for request tracking
        config.headers['X-Correlation-ID'] = this.generateCorrelationId()

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor - Handle token refresh
    this.instance.interceptors.response.use(
      (response) => {
        return response
      },
      async (error) => {
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // If already refreshing, queue the request
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject })
            }).then((token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`
              return this.instance(originalRequest)
            }).catch((err) => {
              return Promise.reject(err)
            })
          }

          originalRequest._retry = true
          this.isRefreshing = true

          try {
            const state = store.getState()
            const refreshToken = state.auth.refreshToken

            if (refreshToken) {
              const result = await store.dispatch(refreshAccessToken())
              
              if (refreshAccessToken.fulfilled.match(result)) {
                const newToken = result.payload.access_token
                this.processQueue(newToken, null)
                originalRequest.headers.Authorization = `Bearer ${newToken}`
                return this.instance(originalRequest)
              }
            }
          } catch (refreshError) {
            this.processQueue(null, refreshError)
            store.dispatch(clearCredentials())
            window.location.href = '/login'
          } finally {
            this.isRefreshing = false
          }
        }

        return Promise.reject(error)
      }
    )
  }

  private processQueue(token: string | null, error: any) {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error)
      } else if (token) {
        resolve(token)
      }
    })

    this.failedQueue = []
  }

  private generateCorrelationId(): string {
    return `qms-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  // HTTP methods
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.get<T>(url, config)
  }

  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.post<T>(url, data, config)
  }

  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.put<T>(url, data, config)
  }

  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.patch<T>(url, data, config)
  }

  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.delete<T>(url, config)
  }

  // File upload with progress
  public async uploadFile<T = any>(
    url: string,
    file: File,
    onProgress?: (progressEvent: any) => void,
    additionalData?: Record<string, any>
  ): Promise<AxiosResponse<T>> {
    const formData = new FormData()
    formData.append('file', file)

    if (additionalData) {
      Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key])
      })
    }

    return this.instance.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onProgress,
    })
  }

  // Download file
  public async downloadFile(url: string, filename?: string): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob',
    })

    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(downloadUrl)
  }

  // Health check
  public async healthCheck(): Promise<AxiosResponse> {
    return this.instance.get('/health')
  }

  // Get API instance for advanced usage
  public getInstance(): AxiosInstance {
    return this.instance
  }
}

export const apiClient = new ApiClient()
export default apiClient