import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface User {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  role: string
  department: string
  is_active: boolean
  last_login?: string
  created_at: string
  permissions: string[]
}

interface UserState {
  users: User[]
  selectedUser: User | null
  filters: {
    role: string[]
    department: string[]
    status: string[]
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

const initialState: UserState = {
  users: [],
  selectedUser: null,
  filters: {
    role: [],
    department: [],
    status: [],
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

const userSlice = createSlice({
  name: 'users',
  initialState,
  reducers: {
    setUsers: (state, action: PayloadAction<User[]>) => {
      state.users = action.payload
    },
    setSelectedUser: (state, action: PayloadAction<User | null>) => {
      state.selectedUser = action.payload
    },
    setFilters: (state, action: PayloadAction<Partial<UserState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    setPagination: (state, action: PayloadAction<Partial<UserState['pagination']>>) => {
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
  setUsers,
  setSelectedUser,
  setFilters,
  setPagination,
  setLoading,
  setError,
  clearFilters,
} = userSlice.actions

export default userSlice