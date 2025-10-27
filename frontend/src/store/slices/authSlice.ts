import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { authService } from '@services/authService'
import { User, LoginCredentials, AuthResponse } from '@types/auth'

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  permissions: string[]
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('qms_token'),
  refreshToken: localStorage.getItem('qms_refresh_token'),
  isAuthenticated: !!localStorage.getItem('qms_token'),
  isLoading: false,
  error: null,
  permissions: [],
}

console.log('Redux: Initial auth state:', {
  hasToken: !!localStorage.getItem('qms_token'),
  isAuthenticated: !!localStorage.getItem('qms_token')
})

// Async thunks for authentication
export const loginUser = createAsyncThunk<
  AuthResponse,
  LoginCredentials,
  { rejectValue: string }
>(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await authService.login(credentials)
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || 'Login failed')
    }
  }
)

export const logoutUser = createAsyncThunk<
  void,
  void,
  { rejectValue: string }
>(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout()
    } catch (error: any) {
      return rejectWithValue(error.message || 'Logout failed')
    }
  }
)

export const refreshAccessToken = createAsyncThunk<
  AuthResponse,
  void,
  { rejectValue: string }
>(
  'auth/refresh',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authService.refreshToken()
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || 'Token refresh failed')
    }
  }
)

export const getCurrentUser = createAsyncThunk<
  User,
  void,
  { rejectValue: string }
>(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const user = await authService.getCurrentUser()
      return user
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to get current user')
    }
  }
)

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    setCredentials: (state, action: PayloadAction<AuthResponse>) => {
      const { user, access_token, refresh_token, permissions } = action.payload
      state.user = user
      state.token = access_token
      state.refreshToken = refresh_token
      state.permissions = permissions || []
      state.isAuthenticated = true
      
      // Store in localStorage
      localStorage.setItem('qms_token', access_token)
      if (refresh_token) {
        localStorage.setItem('qms_refresh_token', refresh_token)
      }
    },
    clearCredentials: (state) => {
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
      state.permissions = []
      
      // Clear localStorage
      localStorage.removeItem('qms_token')
      localStorage.removeItem('qms_refresh_token')
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload }
      }
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        console.log('Redux: loginUser.fulfilled called with payload:', action.payload)
        state.isLoading = false
        state.user = action.payload.user
        state.token = action.payload.access_token
        state.refreshToken = action.payload.refresh_token
        state.permissions = action.payload.permissions || []
        state.isAuthenticated = true
        
        console.log('Redux: State updated to:', {
          isAuthenticated: state.isAuthenticated,
          user: state.user?.username,
          hasToken: !!state.token
        })
        
        // Store in localStorage
        localStorage.setItem('qms_token', action.payload.access_token)
        if (action.payload.refresh_token) {
          localStorage.setItem('qms_refresh_token', action.payload.refresh_token)
        }
        console.log('Redux: Tokens stored in localStorage')
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload || 'Login failed'
        state.isAuthenticated = false
      })
    
    // Logout
    builder
      .addCase(logoutUser.pending, (state) => {
        state.isLoading = true
      })
      .addCase(logoutUser.fulfilled, (state) => {
        state.isLoading = false
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
        state.permissions = []
        
        // Clear localStorage
        localStorage.removeItem('qms_token')
        localStorage.removeItem('qms_refresh_token')
      })
      .addCase(logoutUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload || 'Logout failed'
        // Still clear credentials on logout error
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
        state.permissions = []
        localStorage.removeItem('qms_token')
        localStorage.removeItem('qms_refresh_token')
      })
    
    // Refresh Token
    builder
      .addCase(refreshAccessToken.fulfilled, (state, action) => {
        state.token = action.payload.access_token
        state.user = action.payload.user
        state.permissions = action.payload.permissions || []
        localStorage.setItem('qms_token', action.payload.access_token)
      })
      .addCase(refreshAccessToken.rejected, (state) => {
        // Clear credentials if refresh fails
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
        state.permissions = []
        localStorage.removeItem('qms_token')
        localStorage.removeItem('qms_refresh_token')
      })
    
    // Get Current User
    builder
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.user = action.payload
      })
      .addCase(getCurrentUser.rejected, (state) => {
        // If getting current user fails, clear authentication
        state.user = null
        state.token = null
        state.refreshToken = null
        state.isAuthenticated = false
        state.permissions = []
        localStorage.removeItem('qms_token')
        localStorage.removeItem('qms_refresh_token')
      })
  },
})

export const { clearError, setCredentials, clearCredentials, updateUser } = authSlice.actions
export default authSlice