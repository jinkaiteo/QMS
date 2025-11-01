import { apiClient } from './apiClient'

// Document Types based on backend schema
export interface DocumentType {
  id: number
  uuid: string
  name: string
  code: string
  prefix: string
  description: string
  is_controlled: boolean
  retention_period_years: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DocumentCategory {
  id: number
  uuid: string
  name: string
  code: string
  parent_id?: number
  description: string
  color?: string
  icon?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserInfo {
  id: number
  username: string
  full_name: string
  email: string
}

export interface Document {
  id: number
  uuid?: string
  document_number: string
  title: string
  status: string
  current_version: string
  effective_date?: string
  created_at: string
  updated_at: string
  tags: string[]
  document_type: DocumentType
  category?: DocumentCategory
  author: UserInfo
}

export interface DocumentSearchResponse {
  items: Document[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface CreateDocumentRequest {
  title: string
  description?: string
  document_number: string
  document_type_id: number
  category_id?: number
  confidentiality_level?: string
  is_controlled?: boolean
  tags?: string[]
}

class DocumentsService {
  private readonly baseUrl = '/api/v1/documents'

  // Get all documents with pagination
  async getDocuments(
    page: number = 1,
    perPage: number = 20,
    search?: string,
    status?: string,
    documentTypeId?: number
  ): Promise<DocumentSearchResponse> {
    let url = `${this.baseUrl}/?page=${page}&per_page=${perPage}`
    
    if (search) {
      url += `&search=${encodeURIComponent(search)}`
    }
    if (status) {
      url += `&status=${status}`
    }
    if (documentTypeId) {
      url += `&document_type_id=${documentTypeId}`
    }

    const response = await apiClient.get(url)
    return response.data
  }

  // Get document types
  async getDocumentTypes(): Promise<DocumentType[]> {
    const response = await apiClient.get(`${this.baseUrl}/types`)
    return response.data
  }

  // Get document categories
  async getDocumentCategories(): Promise<DocumentCategory[]> {
    const response = await apiClient.get(`${this.baseUrl}/categories`)
    return response.data
  }

  // Get single document
  async getDocument(id: number): Promise<Document> {
    const response = await apiClient.get(`${this.baseUrl}/${id}`)
    return response.data
  }

  // Create new document
  async createDocument(document: CreateDocumentRequest): Promise<Document> {
    const response = await apiClient.post(`${this.baseUrl}/`, document)
    return response.data
  }

  // Update document
  async updateDocument(id: number, document: Partial<CreateDocumentRequest>): Promise<Document> {
    const response = await apiClient.put(`${this.baseUrl}/${id}`, document)
    return response.data
  }

  // Delete document
  async deleteDocument(id: number): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${id}`)
  }

  // Upload document file
  async uploadDocument(
    file: File,
    metadata: CreateDocumentRequest,
    onProgress?: (progress: number) => void
  ): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('metadata', JSON.stringify(metadata))

    const response = await apiClient.uploadFile(
      `${this.baseUrl}/upload`,
      file,
      onProgress,
      metadata
    )
    return response.data
  }

  // Download document
  async downloadDocument(id: number, filename?: string): Promise<void> {
    const document = await this.getDocument(id)
    const downloadFilename = filename || `${document.document_number}_${document.title}.pdf`
    
    await apiClient.downloadFile(`${this.baseUrl}/${id}/download`, downloadFilename)
  }

  // Get document statistics for dashboard
  async getDocumentStats(): Promise<{
    total: number
    approved: number
    pending_review: number
    draft: number
    expired: number
  }> {
    const response = await apiClient.get(`${this.baseUrl}/stats`)
    return response.data
  }

  // Error handling helper
  handleError(error: any): string {
    if (error.response?.data?.detail) {
      return error.response.data.detail
    }
    if (error.response?.data?.message) {
      return error.response.data.message
    }
    if (error.message) {
      return error.message
    }
    return 'An unexpected error occurred'
  }
}

export const documentsService = new DocumentsService()
export default documentsService