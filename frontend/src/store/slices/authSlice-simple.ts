import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { User, LoginCredentials, AuthResponse, AuthState } from '../../types/auth-simple'
import { authService } from '../../services/authService-simple'

// Initial state
const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('qms_token'),
  refreshToken: localStorage.getItem('qms_refresh_token'),
  isAuthenticated: false,
}

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await authService.login(credentials)
      
      // Store tokens in localStorage
      localStorage.setItem('qms_token', response.access_token)
      if (response.refresh_token) {
        localStorage.setItem('qms_refresh_token', response.refresh_token)
      }
      
      return response
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Login failed')
    }
  }
)

export const logoutUser = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout()
      
      // Clear tokens from localStorage
      localStorage.removeItem('qms_token')
      localStorage.removeItem('qms_refresh_token')
      
      return null
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Logout failed')
    }
  }
)

export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const user = await authService.getCurrentUser()
      return user
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to get user info')
    }
  }
)

// Auth slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearAuth: (state) => {
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
      localStorage.removeItem('qms_token')
      localStorage.removeItem('qms_refresh_token')
    },
    setToken: (state, action: PayloadAction<string>) => {
      state.token = action.payload
      state.isAuthenticated = true
      localStorage.setItem('qms_token', action.payload)
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginUser.fulfilled, (state, action) => {
        state.user = action.payload.user
        state.token = action.payload.access_token
        state.refreshToken = action.payload.refresh_token || null
        state.isAuthenticated = true
      })
      .addCase(loginUser.rejected, (state) => {
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
      })
      // Logout
      .addCase(logoutUser.fulfilled, (state) => {
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
      })
      // Get current user
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.user = action.payload
        state.isAuthenticated = true
      })
      .addCase(getCurrentUser.rejected, (state) => {
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
        localStorage.removeItem('qms_token')
        localStorage.removeItem('qms_refresh_token')
      })
  },
})

export const { clearAuth, setToken } = authSlice.actions
export default authSlice.reducer