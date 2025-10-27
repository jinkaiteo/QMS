import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface Sample {
  id: string
  sample_id: string
  batch_number?: string
  product_name: string
  status: 'received' | 'in_testing' | 'completed' | 'released' | 'rejected'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  received_date: string
  due_date: string
  assigned_to?: string
  test_methods: string[]
}

interface TestResult {
  id: string
  sample_id: string
  test_method: string
  parameter: string
  result: string
  specification: string
  status: 'pass' | 'fail' | 'pending'
  tested_by: string
  tested_date: string
}

interface LIMSState {
  samples: Sample[]
  selectedSample: Sample | null
  testResults: TestResult[]
  filters: {
    status: string[]
    priority: string[]
    dateRange: { start: string | null; end: string | null }
    assignee: string[]
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

const initialState: LIMSState = {
  samples: [],
  selectedSample: null,
  testResults: [],
  filters: {
    status: [],
    priority: [],
    dateRange: { start: null, end: null },
    assignee: [],
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

const limsSlice = createSlice({
  name: 'lims',
  initialState,
  reducers: {
    setSamples: (state, action: PayloadAction<Sample[]>) => {
      state.samples = action.payload
    },
    setSelectedSample: (state, action: PayloadAction<Sample | null>) => {
      state.selectedSample = action.payload
    },
    setTestResults: (state, action: PayloadAction<TestResult[]>) => {
      state.testResults = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<LIMSState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    setPagination: (state, action: PayloadAction<Partial<LIMSState['pagination']>>) => {
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
  setSamples,
  setSelectedSample,
  setTestResults,
  setFilters,
  setPagination,
  setLoading,
  setError,
  clearFilters,
} = limsSlice.actions

export default limsSlice