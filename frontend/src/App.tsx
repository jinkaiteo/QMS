import React, { Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Box, CircularProgress, Typography } from '@mui/material'
import { useSelector } from 'react-redux'
import { RootState } from './store/store'
import Layout from './components/Layout/Layout'

// Lazy load all page components
const LoginPage = React.lazy(() => import('./pages/Auth/LoginPage'))
const DashboardPage = React.lazy(() => import('./pages/Dashboard/DashboardPage'))
const DocumentsPage = React.lazy(() => import('./pages/Documents/DocumentsPage'))
const LIMSPage = React.lazy(() => import('./pages/LIMS/LIMSPage'))
const TrainingPage = React.lazy(() => import('./pages/Training/TrainingPage'))
const QualityPage = React.lazy(() => import('./pages/Quality/QualityPage'))
const UsersPage = React.lazy(() => import('./pages/Users/UsersPage'))
const OrganizationPage = React.lazy(() => import('./pages/Organization/OrganizationPage'))
const SettingsPage = React.lazy(() => import('./pages/Settings/SettingsPage'))

// Phase C: Advanced Analytics Pages
const ExecutiveAnalyticsDashboard = React.lazy(() => import('./pages/Analytics/ExecutiveAnalyticsDashboard'))
const PredictiveSchedulingDashboard = React.lazy(() => import('./pages/Analytics/PredictiveSchedulingDashboard'))
const AdvancedDashboard = React.lazy(() => import('./pages/Analytics/AdvancedDashboard'))
const AnalyticsMainPage = React.lazy(() => import('./pages/Analytics/AnalyticsMainPage'))
const ComplianceDashboard = React.lazy(() => import('./pages/Analytics/ComplianceDashboard'))
const NotificationDashboard = React.lazy(() => import('./pages/Analytics/NotificationDashboard'))

// Simple loading component
const LoadingScreen: React.FC = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
    <CircularProgress />
    <Typography sx={{ ml: 2 }}>Loading QMS Platform...</Typography>
  </Box>
)

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user, token } = useSelector((state: RootState) => state.auth)
  
  console.log('ProtectedRoute - Auth State:', { isAuthenticated, user: user?.username, hasToken: !!token })
  
  if (!isAuthenticated) {
    console.log('Not authenticated, redirecting to login')
    return <Navigate to="/login" replace />
  }
  
  console.log('Authenticated, rendering protected content')
  return <>{children}</>
}

// Public Route Component
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth)
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  
  return <>{children}</>
}

const App: React.FC = () => {
  return (
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
          
          {/* Protected Routes with Layout */}
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
          
          {/* Module Routes with Layout */}
          <Route 
            path="/documents" 
            element={
              <ProtectedRoute>
                <Layout>
                  <DocumentsPage />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/lims" 
            element={
              <ProtectedRoute>
                <Layout>
                  <LIMSPage />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/training" 
            element={
              <ProtectedRoute>
                <Layout>
                  <TrainingPage />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/training/programs" 
            element={
              <ProtectedRoute>
                <Layout>
                  <TrainingPage />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/training/assignments" 
            element={
              <ProtectedRoute>
                <Layout>
                  <TrainingPage />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/quality" 
            element={
              <ProtectedRoute>
                <Layout>
                  <QualityPage />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/users" 
            element={
              <ProtectedRoute>
                <Layout>
                  <UsersPage />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/organization" 
            element={
              <ProtectedRoute>
                <Layout>
                  <OrganizationPage />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/settings" 
            element={
              <ProtectedRoute>
                <Layout>
                  <SettingsPage />
                </Layout>
              </ProtectedRoute>
            } 
          />
          
          {/* Phase C: Advanced Analytics Routes */}
          <Route 
            path="/analytics" 
            element={
              <ProtectedRoute>
                <Layout>
                  <AnalyticsMainPage />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/analytics/executive" 
            element={
              <ProtectedRoute>
                <Layout>
                  <ExecutiveAnalyticsDashboard />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/analytics/predictive-scheduling" 
            element={
              <ProtectedRoute>
                <Layout>
                  <PredictiveSchedulingDashboard />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/analytics/advanced" 
            element={
              <ProtectedRoute>
                <Layout>
                  <AdvancedDashboard />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/compliance" 
            element={
              <ProtectedRoute>
                <Layout>
                  <ComplianceDashboard />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/notifications" 
            element={
              <ProtectedRoute>
                <Layout>
                  <NotificationDashboard />
                </Layout>
              </ProtectedRoute>
            } 
          />
          
          {/* Default route */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* 404 */}
          <Route path="*" element={
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h4">404 - Page Not Found</Typography>
              <Typography>Return to <a href="/dashboard">Dashboard</a></Typography>
            </Box>
          } />
        </Routes>
      </Suspense>
    </Box>
  )
}

export default App