import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface Document {
  id: string
  title: string
  version: string
  status: 'draft' | 'under_review' | 'approved' | 'archived'
  type: string
  created_at: string
  updated_at: string
  created_by: string
  file_path?: string
  file_size?: number
  file_type?: string
}

interface DocumentState {
  documents: Document[]
  selectedDocument: Document | null
  filters: {
    status: string[]
    type: string[]
    dateRange: { start: string | null; end: string | null }
    search: string
  }
  pagination: {
    page: number
    limit: number
    total: number
  }
  loading: boolean
  error: string | null
}

const initialState: DocumentState = {
  documents: [],
  selectedDocument: null,
  filters: {
    status: [],
    type: [],
    dateRange: { start: null, end: null },
    search: '',
  },
  pagination: {
    page: 1,
    limit: 25,
    total: 0,
  },
  loading: false,
  error: null,
}

const documentSlice = createSlice({
  name: 'documents',
  initialState,
  reducers: {
    setDocuments: (state, action: PayloadAction<Document[]>) => {
      state.documents = action.payload
    },
    setSelectedDocument: (state, action: PayloadAction<Document | null>) => {
      state.selectedDocument = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<DocumentState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    setPagination: (state, action: PayloadAction<Partial<DocumentState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    clearFilters: (state) => {
      state.filters = initialState.filters
    },
  },
})

export const {
  setDocuments,
  setSelectedDocument,
  setFilters,
  setPagination,
  setLoading,
  setError,
  clearFilters,
} = documentSlice.actions

export default documentSlice