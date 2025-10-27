import React, { useEffect } from 'react'
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  LinearProgress,
  IconButton,
} from '@mui/material'
import {
  Dashboard,
  TrendingUp,
  Warning,
  CheckCircle,
  Assignment,
  Science,
  School,
  People,
  Refresh,
  ArrowForward,
} from '@mui/icons-material'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'

import { RootState } from '@store/store'
import { setPageTitle, setBreadcrumbs } from '@store/slices/uiSlice'
import { authService } from '@services/authService'

const DashboardPage: React.FC = () => {
  console.log('DashboardPage component rendering')
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { user } = useSelector((state: RootState) => state.auth)

  useEffect(() => {
    dispatch(setPageTitle('Dashboard'))
    dispatch(setBreadcrumbs([
      { label: 'Dashboard' }
    ]))
  }, [dispatch])

  const userDisplayName = authService.getUserDisplayName(user)

  // Mock dashboard data (in a real app, this would come from API)
  const dashboardStats = {
    documents: { total: 1247, pending: 23, approved: 1198, rejected: 26 },
    samples: { total: 89, inTesting: 34, completed: 45, released: 10 },
    training: { total: 156, overdue: 8, expiring: 12, completed: 136 },
    quality: { total: 45, open: 12, investigating: 8, closed: 25 },
  }

  const recentActivities = [
    { id: 1, type: 'document', action: 'Document "SOP-001" approved', time: '2 hours ago' },
    { id: 2, type: 'sample', action: 'Sample "S-2024-001" completed testing', time: '4 hours ago' },
    { id: 3, type: 'training', action: 'Training "GMP Basics" assigned to John Doe', time: '1 day ago' },
    { id: 4, type: 'quality', action: 'CAPA "C-2024-005" effectiveness verified', time: '2 days ago' },
  ]

  const quickActions = [
    { label: 'Manage Documents', icon: <Assignment />, path: '/documents', permission: 'documents.view' },
    { label: 'LIMS Dashboard', icon: <Science />, path: '/lims', permission: 'lims.view' },
    { label: 'Training Management', icon: <School />, path: '/training', permission: 'training.view' },
    { label: 'Quality Management', icon: <Warning />, path: '/quality', permission: 'quality.view' },
  ]

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
      case 'completed':
      case 'released':
      case 'closed':
        return 'success'
      case 'pending':
      case 'in_testing':
      case 'investigating':
        return 'warning'
      case 'rejected':
      case 'overdue':
      case 'open':
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <Box>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          Welcome back, {userDisplayName}
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Here's what's happening in your QMS platform today.
        </Typography>
      </Box>

      {/* Dashboard Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Documents */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Assignment sx={{ color: 'primary.main', mr: 1 }} />
                <Typography variant="h6">Documents</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
                {dashboardStats.documents.total}
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Pending: {dashboardStats.documents.pending}</Typography>
                  <Typography variant="body2">Approved: {dashboardStats.documents.approved}</Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={(dashboardStats.documents.approved / dashboardStats.documents.total) * 100}
                  sx={{ height: 6, borderRadius: 3 }}
                />
              </Box>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/documents')}>
                View All <ArrowForward sx={{ ml: 1, fontSize: 16 }} />
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Samples */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Science sx={{ color: 'info.main', mr: 1 }} />
                <Typography variant="h6">LIMS Samples</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
                {dashboardStats.samples.total}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label={`Testing: ${dashboardStats.samples.inTesting}`} size="small" color="warning" />
                <Chip label={`Released: ${dashboardStats.samples.released}`} size="small" color="success" />
              </Box>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/lims')}>
                View LIMS <ArrowForward sx={{ ml: 1, fontSize: 16 }} />
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Training */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <School sx={{ color: 'success.main', mr: 1 }} />
                <Typography variant="h6">Training</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
                {dashboardStats.training.total}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label={`Overdue: ${dashboardStats.training.overdue}`} size="small" color="error" />
                <Chip label={`Expiring: ${dashboardStats.training.expiring}`} size="small" color="warning" />
              </Box>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/training')}>
                View Training <ArrowForward sx={{ ml: 1, fontSize: 16 }} />
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Quality Events */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Warning sx={{ color: 'warning.main', mr: 1 }} />
                <Typography variant="h6">Quality Events</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
                {dashboardStats.quality.total}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label={`Open: ${dashboardStats.quality.open}`} size="small" color="error" />
                <Chip label={`Investigating: ${dashboardStats.quality.investigating}`} size="small" color="warning" />
              </Box>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/quality')}>
                View Quality <ArrowForward sx={{ ml: 1, fontSize: 16 }} />
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <TrendingUp sx={{ mr: 1 }} />
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              {quickActions
                .filter(action => !action.permission || authService.hasPermission(user, action.permission))
                .map((action, index) => (
                <Grid item xs={12} sm={6} key={index}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={action.icon}
                    onClick={() => navigate(action.path)}
                    sx={{ 
                      py: 2,
                      justifyContent: 'flex-start',
                      textAlign: 'left',
                    }}
                  >
                    {action.label}
                  </Button>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Recent Activities */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                <Dashboard sx={{ mr: 1 }} />
                Recent Activities
              </Typography>
              <IconButton size="small">
                <Refresh />
              </IconButton>
            </Box>
            <Box>
              {recentActivities.map((activity) => (
                <Box
                  key={activity.id}
                  sx={{
                    p: 2,
                    mb: 1,
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                >
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    {activity.action}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {activity.time}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default DashboardPage