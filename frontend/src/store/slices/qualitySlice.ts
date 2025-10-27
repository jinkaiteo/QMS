import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface QualityEvent {
  id: string
  event_type: 'deviation' | 'ooo' | 'complaint' | 'incident'
  title: string
  description: string
  severity: 'critical' | 'major' | 'minor' | 'low'
  status: 'open' | 'investigating' | 'capa_required' | 'closed'
  reported_by: string
  reported_date: string
  due_date: string
  assigned_to?: string
  product_affected?: string
}

interface CAPA {
  id: string
  title: string
  source_event_id?: string
  root_cause: string
  corrective_action: string
  preventive_action: string
  status: 'open' | 'implementation' | 'verification' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  assigned_to: string
  due_date: string
  effectiveness_verified: boolean
}

interface QualityState {
  events: QualityEvent[]
  capas: CAPA[]
  selectedEvent: QualityEvent | null
  selectedCapa: CAPA | null
  filters: {
    eventType: string[]
    severity: string[]
    status: string[]
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

const initialState: QualityState = {
  events: [],
  capas: [],
  selectedEvent: null,
  selectedCapa: null,
  filters: {
    eventType: [],
    severity: [],
    status: [],
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

const qualitySlice = createSlice({
  name: 'quality',
  initialState,
  reducers: {
    setEvents: (state, action: PayloadAction<QualityEvent[]>) => {
      state.events = action.payload
    },
    setCapas: (state, action: PayloadAction<CAPA[]>) => {
      state.capas = action.payload
    },
    setSelectedEvent: (state, action: PayloadAction<QualityEvent | null>) => {
      state.selectedEvent = action.payload
    },
    setSelectedCapa: (state, action: PayloadAction<CAPA | null>) => {
      state.selectedCapa = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<QualityState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    setPagination: (state, action: PayloadAction<Partial<QualityState['pagination']>>) => {
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
  setEvents,
  setCapas,
  setSelectedEvent,
  setSelectedCapa,
  setFilters,
  setPagination,
  setLoading,
  setError,
  clearFilters,
} = qualitySlice.actions

export default qualitySlice