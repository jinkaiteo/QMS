import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, CssBaseline, Box } from '@mui/material'
import { Provider } from 'react-redux'
import { store } from './store/store-simple'
import { theme } from './theme'

// Simple components without complex dependencies
import LoginPage from './pages/Auth/LoginPage-Simple'
import DashboardPage from './pages/Dashboard/DashboardPage-Simple'
import Layout from './components/Layout/Layout-Simple'
import { useSelector } from 'react-redux'
import { RootState } from './store/store-simple'

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, token } = useSelector((state: RootState) => state.auth)
  
  if (!user || !token) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

// Main App Component
const AppContent: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth)

  return (
    <Routes>
      <Route 
        path="/login" 
        element={
          user ? <Navigate to="/dashboard" replace /> : <LoginPage />
        } 
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout>
              <DashboardPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/training"
        element={
          <ProtectedRoute>
            <Layout>
              <DashboardPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box sx={{ width: '100%', height: '100vh' }}>
          <AppContent />
        </Box>
      </ThemeProvider>
    </Provider>
  )
}

export default App