import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface TrainingRecord {
  id: string
  employee_id: string
  employee_name: string
  training_title: string
  training_type: 'initial' | 'refresher' | 'continuing' | 'specialized'
  status: 'scheduled' | 'in_progress' | 'completed' | 'expired' | 'overdue'
  scheduled_date: string
  completion_date?: string
  expiry_date?: string
  trainer: string
  score?: number
  certification_required: boolean
}

interface TrainingSlice {
  records: TrainingRecord[]
  selectedRecord: TrainingRecord | null
  filters: {
    status: string[]
    type: string[]
    employee: string[]
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

const initialState: TrainingSlice = {
  records: [],
  selectedRecord: null,
  filters: {
    status: [],
    type: [],
    employee: [],
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

const trainingSlice = createSlice({
  name: 'training',
  initialState,
  reducers: {
    setRecords: (state, action: PayloadAction<TrainingRecord[]>) => {
      state.records = action.payload
    },
    setSelectedRecord: (state, action: PayloadAction<TrainingRecord | null>) => {
      state.selectedRecord = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<TrainingSlice['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    setPagination: (state, action: PayloadAction<Partial<TrainingSlice['pagination']>>) => {
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
  setRecords,
  setSelectedRecord,
  setFilters,
  setPagination,
  setLoading,
  setError,
  clearFilters,
} = trainingSlice.actions

export default trainingSlice