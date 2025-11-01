import React, { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material'
import {
  School as TrainingIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CompleteIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material'
import { RootState } from '../../store/store-simple'
import { apiClient } from '../../services/apiClient-simple'

interface TrainingAssignment {
  id: number
  program_id: number
  employee_id: number
  status: string
  progress: number
  score?: number
  due_date: string
  created_at: string
}

interface TrainingProgram {
  id: number
  title: string
  type: string
  duration: number
  status: string
  description?: string
}

const DashboardPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth)
  const [assignments, setAssignments] = useState<TrainingAssignment[]>([])
  const [programs, setPrograms] = useState<TrainingProgram[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Load training assignments
      const assignmentsResponse = await apiClient.get<TrainingAssignment[]>('/v1/training/assignments')
      setAssignments(assignmentsResponse.data)
      
      // Load training programs
      const programsResponse = await apiClient.get<TrainingProgram[]>('/v1/training/programs')
      setPrograms(programsResponse.data)
      
    } catch (err: any) {
      setError('Failed to load dashboard data')
      console.error('Dashboard error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'in_progress': return 'primary'
      case 'assigned': return 'warning'
      case 'overdue': return 'error'
      default: return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CompleteIcon />
      case 'in_progress': return <PendingIcon />
      case 'assigned': return <AssignmentIcon />
      default: return <AssignmentIcon />
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Welcome back, {user?.first_name || user?.username}!
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          QMS Platform Dashboard - Training & Compliance Overview
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrainingIcon color="primary" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography variant="h4" color="primary">
                    {programs.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Training Programs
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <AssignmentIcon color="info" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography variant="h4" color="info.main">
                    {assignments.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    My Assignments
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <CompleteIcon color="success" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography variant="h4" color="success.main">
                    {assignments.filter(a => a.status === 'completed').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completed
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <PendingIcon color="warning" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography variant="h4" color="warning.main">
                    {assignments.filter(a => a.status === 'assigned' || a.status === 'in_progress').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Pending
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Training Assignments */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                My Training Assignments
              </Typography>
              
              {assignments.length === 0 ? (
                <Typography color="text.secondary">
                  No training assignments found.
                </Typography>
              ) : (
                <List>
                  {assignments.map((assignment) => {
                    const program = programs.find(p => p.id === assignment.program_id)
                    return (
                      <ListItem key={assignment.id} divider>
                        <ListItemIcon>
                          {getStatusIcon(assignment.status)}
                        </ListItemIcon>
                        <ListItemText
                          primary={program?.title || `Program ${assignment.program_id}`}
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                Progress: {assignment.progress}% | Due: {new Date(assignment.due_date).toLocaleDateString()}
                              </Typography>
                              {assignment.score && (
                                <Typography variant="body2" color="text.secondary">
                                  Score: {assignment.score}%
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                        <Chip
                          label={assignment.status.replace('_', ' ').toUpperCase()}
                          color={getStatusColor(assignment.status) as any}
                          size="small"
                        />
                      </ListItem>
                    )
                  })}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Available Training Programs
              </Typography>
              
              {programs.length === 0 ? (
                <Typography color="text.secondary">
                  No training programs available.
                </Typography>
              ) : (
                <List>
                  {programs.slice(0, 5).map((program) => (
                    <ListItem key={program.id} divider>
                      <ListItemIcon>
                        <TrainingIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={program.title}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {program.description || 'No description available'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Duration: {program.duration} hours | Type: {program.type}
                            </Typography>
                          </Box>
                        }
                      />
                      <Chip
                        label={program.status.toUpperCase()}
                        color={program.status === 'active' ? 'success' : 'default'}
                        size="small"
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={() => window.location.href = '/training'}
          sx={{ mr: 2 }}
        >
          View All Training
        </Button>
        <Button
          variant="outlined"
          size="large"
          onClick={loadDashboardData}
        >
          Refresh Data
        </Button>
      </Box>
    </Box>
  )
}

export default DashboardPage