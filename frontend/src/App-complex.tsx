import React, { Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Box, CircularProgress, Typography } from '@mui/material'
import { useSelector } from 'react-redux'

import { RootState } from '@store/store'
import Layout from '@components/Layout/Layout'
import LoadingScreen from '@components/Common/LoadingScreen'
import ErrorBoundary from '@components/Common/ErrorBoundary'

// Lazy load pages for better performance
const LoginPage = React.lazy(() => import('@pages/Auth/LoginPage'))
const DashboardPage = React.lazy(() => import('@pages/Dashboard/DashboardPage'))
const DocumentsPage = React.lazy(() => import('@pages/Documents/DocumentsPage'))
const LIMSPage = React.lazy(() => import('@pages/LIMS/LIMSPage'))
const TrainingPage = React.lazy(() => import('@pages/Training/TrainingPage'))
const QualityPage = React.lazy(() => import('@pages/Quality/QualityPage'))
const UsersPage = React.lazy(() => import('@pages/Users/UsersPage'))
const SettingsPage = React.lazy(() => import('@pages/Settings/SettingsPage'))
const NotFoundPage = React.lazy(() => import('@pages/Error/NotFoundPage'))

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth)
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

// Public Route Component (redirects if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth)
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  
  return <>{children}</>
}

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Suspense fallback={<LoadingScreen />}>
          <Routes>
            {/* Public Routes */}
            <Route 
              path="/login" 
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              } 
            />
            
            {/* Protected Routes */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              {/* Dashboard */}
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              
              {/* Document Management (EDMS) */}
              <Route path="documents/*" element={<DocumentsPage />} />
              
              {/* Laboratory Information Management (LIMS) */}
              <Route path="lims/*" element={<LIMSPage />} />
              
              {/* Training Records Management (TRM) */}
              <Route path="training/*" element={<TrainingPage />} />
              
              {/* Quality Management (QRM, CAPA) */}
              <Route path="quality/*" element={<QualityPage />} />
              
              {/* User Management */}
              <Route path="users/*" element={<UsersPage />} />
              
              {/* System Settings */}
              <Route path="settings/*" element={<SettingsPage />} />
            </Route>
            
            {/* 404 Not Found */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </Box>
    </ErrorBoundary>
  )
}

export default App