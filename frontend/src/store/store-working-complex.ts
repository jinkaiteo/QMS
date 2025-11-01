import { configureStore } from '@reduxjs/toolkit'

// Import slices individually to avoid circular dependencies
import authSlice from './slices/authSlice-simple'

// Create individual slice reducers
const authReducer = authSlice

// Simple UI slice
const uiSlice = {
  reducer: (state = { sidebarOpen: true, sidebarCollapsed: false, loading: false, pageTitle: 'QMS Platform', notifications: [] }, action: any) => {
    switch (action.type) {
      case 'ui/setSidebarOpen':
        return { ...state, sidebarOpen: action.payload }
      case 'ui/setSidebarCollapsed':
        return { ...state, sidebarCollapsed: action.payload }
      case 'ui/setLoading':
        return { ...state, loading: action.payload }
      case 'ui/setPageTitle':
        return { ...state, pageTitle: action.payload }
      default:
        return state
    }
  }
}

// Simple document slice
const documentSlice = {
  reducer: (state = { documents: [], loading: false, error: null }, action: any) => {
    switch (action.type) {
      case 'documents/setLoading':
        return { ...state, loading: action.payload }
      default:
        return state
    }
  }
}

// Simple training slice
const trainingSlice = {
  reducer: (state = { programs: [], assignments: [], loading: false }, action: any) => {
    switch (action.type) {
      case 'training/setLoading':
        return { ...state, loading: action.payload }
      default:
        return state
    }
  }
}

// Simple quality slice
const qualitySlice = {
  reducer: (state = { events: [], capas: [], loading: false }, action: any) => {
    switch (action.type) {
      case 'quality/setLoading':
        return { ...state, loading: action.payload }
      default:
        return state
    }
  }
}

// Simple lims slice
const limsSlice = {
  reducer: (state = { samples: [], tests: [], loading: false }, action: any) => {
    switch (action.type) {
      case 'lims/setLoading':
        return { ...state, loading: action.payload }
      default:
        return state
    }
  }
}

// Simple users slice
const userSlice = {
  reducer: (state = { users: [], loading: false }, action: any) => {
    switch (action.type) {
      case 'users/setLoading':
        return { ...state, loading: action.payload }
      default:
        return state
    }
  }
}

export const store = configureStore({
  reducer: {
    auth: authReducer,
    ui: uiSlice.reducer,
    documents: documentSlice.reducer,
    lims: limsSlice.reducer,
    training: trainingSlice.reducer,
    quality: qualitySlice.reducer,
    users: userSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export default store