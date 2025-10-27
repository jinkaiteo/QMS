import { configureStore, createSlice, PayloadAction } from '@reduxjs/toolkit'

// Simple auth state
interface AuthState {
  isAuthenticated: boolean
  user: any | null
  token: string | null
  loading: boolean
}

const initialAuthState: AuthState = {
  isAuthenticated: !!localStorage.getItem('qms_token'),
  user: null,
  token: localStorage.getItem('qms_token'),
  loading: false,
}

// Simple auth slice
const authSlice = createSlice({
  name: 'auth',
  initialState: initialAuthState,
  reducers: {
    loginStart: (state) => {
      state.loading = true
    },
    loginSuccess: (state, action: PayloadAction<{ user: any; token: string }>) => {
      state.isAuthenticated = true
      state.user = action.payload.user
      state.token = action.payload.token
      state.loading = false
      localStorage.setItem('qms_token', action.payload.token)
    },
    loginFailure: (state) => {
      state.loading = false
      state.isAuthenticated = false
    },
    logout: (state) => {
      state.isAuthenticated = false
      state.user = null
      state.token = null
      state.loading = false
      localStorage.removeItem('qms_token')
    },
  },
})

// Simple UI state
interface UIState {
  sidebarOpen: boolean
  loading: boolean
  pageTitle: string
}

const initialUIState: UIState = {
  sidebarOpen: true,
  loading: false,
  pageTitle: 'QMS Platform',
}

const uiSlice = createSlice({
  name: 'ui',
  initialState: initialUIState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setPageTitle: (state, action: PayloadAction<string>) => {
      state.pageTitle = action.payload
      document.title = `${action.payload} - QMS Platform v3.0`
    },
  },
})

// Create store
export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    ui: uiSlice.reducer,
  },
  devTools: process.env.NODE_ENV !== 'production',
})

// Export actions
export const { loginStart, loginSuccess, loginFailure, logout } = authSlice.actions
export const { toggleSidebar, setLoading, setPageTitle } = uiSlice.actions

// Export types
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export default store