import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  autoHide?: boolean
  duration?: number
}

interface UIState {
  sidebarOpen: boolean
  sidebarCollapsed: boolean
  loading: boolean
  notifications: Notification[]
  theme: 'light' | 'dark'
  pageTitle: string
  breadcrumbs: Array<{ label: string; path?: string }>
}

const initialState: UIState = {
  sidebarOpen: true,
  sidebarCollapsed: false,
  loading: false,
  notifications: [],
  theme: 'light',
  pageTitle: 'QMS Platform',
  breadcrumbs: [],
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload
    },
    toggleSidebarCollapsed: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id'>>) => {
      const notification: Notification = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        autoHide: true,
        duration: 5000,
        ...action.payload,
      }
      state.notifications.push(notification)
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(
        (notification) => notification.id !== action.payload
      )
    },
    clearNotifications: (state) => {
      state.notifications = []
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload
    },
    setPageTitle: (state, action: PayloadAction<string>) => {
      state.pageTitle = action.payload
      document.title = `${action.payload} - QMS Platform v3.0`
    },
    setBreadcrumbs: (state, action: PayloadAction<Array<{ label: string; path?: string }>>) => {
      state.breadcrumbs = action.payload
    },
  },
})

export const {
  toggleSidebar,
  setSidebarOpen,
  toggleSidebarCollapsed,
  setSidebarCollapsed,
  setLoading,
  addNotification,
  removeNotification,
  clearNotifications,
  setTheme,
  setPageTitle,
  setBreadcrumbs,
} = uiSlice.actions

export default uiSlice