import { configureStore, createSlice } from '@reduxjs/toolkit'

// Simple auth state
interface AuthState {
  user: any | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
}

const initialAuthState: AuthState = {
  user: null,
  token: localStorage.getItem('qms_token'),
  isAuthenticated: false,
  loading: false,
}

const authSlice = createSlice({
  name: 'auth',
  initialState: initialAuthState,
  reducers: {
    loginStart: (state) => {
      state.loading = true
    },
    loginSuccess: (state, action) => {
      state.loading = false
      state.isAuthenticated = true
      state.user = action.payload.user
      state.token = action.payload.access_token
      localStorage.setItem('qms_token', action.payload.access_token)
    },
    loginFailure: (state) => {
      state.loading = false
      state.isAuthenticated = false
      state.user = null
      state.token = null
      localStorage.removeItem('qms_token')
    },
    logout: (state) => {
      state.isAuthenticated = false
      state.user = null
      state.token = null
      localStorage.removeItem('qms_token')
    },
  },
})

export const { loginStart, loginSuccess, loginFailure, logout } = authSlice.actions

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export default store