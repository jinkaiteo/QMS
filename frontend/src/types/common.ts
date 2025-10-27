// Common types used across the QMS Platform v3.0

export interface ApiResponse<T = any> {
  data: T
  message?: string
  success: boolean
  errors?: Record<string, string[]>
  meta?: {
    page?: number
    limit?: number
    total?: number
    total_pages?: number
  }
}

export interface PaginationParams {
  page?: number
  limit?: number
  offset?: number
}

export interface SortParams {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface FilterParams {
  search?: string
  status?: string[]
  date_from?: string
  date_to?: string
  [key: string]: any
}

export interface QueryParams extends PaginationParams, SortParams, FilterParams {}

// Generic CRUD operations
export interface CreateRequest<T> {
  data: Partial<T>
}

export interface UpdateRequest<T> {
  id: string
  data: Partial<T>
}

export interface DeleteRequest {
  id: string
}

export interface BulkDeleteRequest {
  ids: string[]
}

// File upload types
export interface FileUpload {
  file: File
  name?: string
  description?: string
  category?: string
}

export interface UploadedFile {
  id: string
  name: string
  original_name: string
  size: number
  type: string
  url: string
  created_at: string
  created_by: string
}

// Audit trail
export interface AuditLog {
  id: string
  table_name: string
  record_id: string
  action: 'create' | 'update' | 'delete' | 'view'
  old_values?: Record<string, any>
  new_values?: Record<string, any>
  user_id: string
  user_name: string
  timestamp: string
  ip_address: string
  reason?: string
}

// Status types
export type DocumentStatus = 'draft' | 'under_review' | 'approved' | 'archived' | 'obsolete'
export type QualityEventStatus = 'open' | 'investigating' | 'capa_required' | 'closed'
export type CAPAStatus = 'open' | 'implementation' | 'verification' | 'closed'
export type TrainingStatus = 'scheduled' | 'in_progress' | 'completed' | 'expired' | 'overdue'
export type SampleStatus = 'received' | 'in_testing' | 'completed' | 'released' | 'rejected'

// Priority levels
export type Priority = 'low' | 'medium' | 'high' | 'urgent'

// Severity levels for quality events
export type Severity = 'critical' | 'major' | 'minor' | 'low'

// Pharmaceutical compliance types
export interface ComplianceCheck {
  id: string
  type: '21_cfr_part_11' | 'eu_gmp_annex_11' | 'iso_13485' | 'ich_q7'
  requirement: string
  status: 'compliant' | 'non_compliant' | 'not_applicable'
  evidence?: string
  last_checked: string
  next_check_due: string
}

// Electronic signature
export interface ElectronicSignature {
  id: string
  user_id: string
  user_name: string
  role: string
  action: string
  timestamp: string
  ip_address: string
  meaning: string // What the signature means (e.g., "Approved", "Reviewed")
  is_valid: boolean
}

// Data integrity check
export interface DataIntegrityCheck {
  id: string
  table_name: string
  record_id: string
  checksum: string
  verified_at: string
  verified_by: string
  status: 'valid' | 'invalid' | 'pending'
}