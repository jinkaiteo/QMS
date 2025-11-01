import React, { useState } from 'react'
import { 
  Box, 
  Container, 
  Paper, 
  Typography, 
  TextField, 
  Button, 
  Alert,
  AppBar,
  Toolbar,
  Card,
  CardContent,
  Grid,
  IconButton
} from '@mui/material'
import { Menu as MenuIcon } from '@mui/icons-material'
import Sidebar from './components/Layout/Sidebar-Working'
import EnhancedDashboard from './components/Dashboard/EnhancedDashboard'
import DocumentsPage from './pages/Documents/DocumentsPage-Functional'
import TrainingPage from './pages/Training/TrainingPage-Functional'
import QualityPage from './pages/Quality/QualityPage-Functional'
import LIMSPage from './pages/LIMS/LIMSPage-Functional'
import AdvancedReporting from './components/Analytics/AdvancedReporting'
import { NotificationProvider, NotificationBell, useNotifications } from './components/Common/NotificationSystem'

const LoginForm: React.FC<{ onLogin: (user: any) => void }> = ({ onLogin }) => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      if (response.ok) {
        const data = await response.json()
        onLogin({ username, token: data.access_token })
      } else {
        setError('Invalid credentials')
      }
    } catch (err) {
      setError('Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={6} sx={{ p: 4, width: '100%' }}>
          <Typography variant="h4" align="center" gutterBottom>
            QMS Platform v3.0
          </Typography>
          <Typography variant="subtitle1" align="center" color="textSecondary" sx={{ mb: 3 }}>
            Pharmaceutical Quality Management System
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              required
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={loading}
              sx={{ mt: 3, mb: 2 }}
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </Button>
          </Box>

          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="body2" align="center">
              <strong>Demo:</strong> admin / admin123
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}

const Dashboard: React.FC<{ user: any, onLogout: () => void }> = ({ user, onLogout }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [currentPage, setCurrentPage] = useState('/dashboard')

  // Listen for navigation events from sidebar
  React.useEffect(() => {
    const handleNavigation = (event: any) => {
      setCurrentPage(event.detail.path)
    }
    
    window.addEventListener('qms-navigate', handleNavigation)
    return () => window.removeEventListener('qms-navigate', handleNavigation)
  }, [])

  const renderCurrentPage = () => {
    switch (currentPage) {
      case '/documents':
        return <DocumentsPage />
      case '/training':
        return <TrainingPage />
      case '/quality':
        return <QualityPage />
      case '/lims':
        return <LIMSPage />
      case '/settings':
        return <AdvancedReporting />
      case '/dashboard':
      default:
        return <EnhancedDashboard user={user} />
    }
  }

  const getPageTitle = () => {
    switch (currentPage) {
      case '/documents':
        return 'Document Management'
      case '/training':
        return 'Training Management'
      case '/quality':
        return 'Quality Management'
      case '/lims':
        return 'Laboratory (LIMS)'
      case '/settings':
        return 'Advanced Reporting'
      case '/dashboard':
      default:
        return 'Dashboard'
    }
  }

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={() => setSidebarOpen(true)}
            edge="start"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            QMS Platform - {getPageTitle()} - Welcome {user.username}
          </Typography>
          <NotificationBell />
          <Button color="inherit" onClick={onLogout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      <Sidebar 
        open={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        currentPath={currentPage}
      />

      {renderCurrentPage()}
    </Box>
  )
}

const App: React.FC = () => {
  const [user, setUser] = useState<any>(null)

  const handleLogin = (userData: any) => {
    setUser(userData)
  }

  const handleLogout = () => {
    setUser(null)
  }

  return (
    <NotificationProvider>
      <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5' }}>
        {user ? (
          <Dashboard user={user} onLogout={handleLogout} />
        ) : (
          <LoginForm onLogin={handleLogin} />
        )}
      </Box>
    </NotificationProvider>
  )
}

export default App