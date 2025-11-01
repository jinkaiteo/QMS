import React, { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Avatar,
} from '@mui/material'
import {
  Add,
  Visibility,
  Edit,
  Assignment,
  School,
  People,
  Schedule,
  CheckCircle,
  Warning,
  Refresh,
  PlayArrow,
} from '@mui/icons-material'

interface TrainingProgram {
  id: string
  title: string
  type: string
  status: 'active' | 'draft' | 'completed' | 'expired'
  duration: string
  assignedUsers: number
  completionRate: number
  dueDate: string
  instructor: string
}

interface TrainingAssignment {
  id: string
  programTitle: string
  assignee: string
  status: 'not_started' | 'in_progress' | 'completed' | 'overdue'
  progress: number
  dueDate: string
  completedDate?: string
}

const TrainingPage: React.FC = () => {
  const [programs, setPrograms] = useState<TrainingProgram[]>([])
  const [assignments, setAssignments] = useState<TrainingAssignment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'programs' | 'assignments'>('programs')
  const [newProgram, setNewProgram] = useState({
    title: '',
    type: 'GMP',
    duration: '',
    description: '',
  })

  // Mock training data
  const mockPrograms: TrainingProgram[] = [
    {
      id: '1',
      title: 'Good Manufacturing Practices (GMP) - Level 1',
      type: 'GMP',
      status: 'active',
      duration: '4 hours',
      assignedUsers: 24,
      completionRate: 87,
      dueDate: '2024-11-15T00:00:00Z',
      instructor: 'Dr. Sarah Johnson'
    },
    {
      id: '2',
      title: 'Quality Control Laboratory Procedures',
      type: 'Quality Control',
      status: 'active',
      duration: '6 hours',
      assignedUsers: 12,
      completionRate: 92,
      dueDate: '2024-11-20T00:00:00Z',
      instructor: 'Michael Chen'
    },
    {
      id: '3',
      title: 'Cleanroom Behavior and Contamination Control',
      type: 'Safety',
      status: 'active',
      duration: '3 hours',
      assignedUsers: 18,
      completionRate: 78,
      dueDate: '2024-11-10T00:00:00Z',
      instructor: 'Emma Rodriguez'
    },
    {
      id: '4',
      title: 'Equipment Calibration and Maintenance',
      type: 'Technical',
      status: 'draft',
      duration: '5 hours',
      assignedUsers: 0,
      completionRate: 0,
      dueDate: '2024-12-01T00:00:00Z',
      instructor: 'James Wilson'
    }
  ]

  const mockAssignments: TrainingAssignment[] = [
    {
      id: '1',
      programTitle: 'Good Manufacturing Practices (GMP) - Level 1',
      assignee: 'John Doe',
      status: 'completed',
      progress: 100,
      dueDate: '2024-11-15T00:00:00Z',
      completedDate: '2024-10-25T14:30:00Z'
    },
    {
      id: '2',
      programTitle: 'Quality Control Laboratory Procedures',
      assignee: 'Jane Smith',
      status: 'in_progress',
      progress: 65,
      dueDate: '2024-11-20T00:00:00Z'
    },
    {
      id: '3',
      programTitle: 'Cleanroom Behavior and Contamination Control',
      assignee: 'Bob Johnson',
      status: 'overdue',
      progress: 30,
      dueDate: '2024-10-30T00:00:00Z'
    },
    {
      id: '4',
      programTitle: 'Good Manufacturing Practices (GMP) - Level 1',
      assignee: 'Alice Brown',
      status: 'not_started',
      progress: 0,
      dueDate: '2024-11-15T00:00:00Z'
    }
  ]

  useEffect(() => {
    const fetchTrainingData = async () => {
      try {
        setLoading(true)
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        setPrograms(mockPrograms)
        setAssignments(mockAssignments)
        setError(null)
      } catch (err) {
        setError('Failed to load training data')
      } finally {
        setLoading(false)
      }
    }

    fetchTrainingData()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
        return 'success'
      case 'in_progress':
        return 'info'
      case 'draft':
        return 'warning'
      case 'expired':
      case 'overdue':
        return 'error'
      default:
        return 'default'
    }
  }

  const getAssignmentStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'in_progress':
        return 'info'
      case 'not_started':
        return 'warning'
      case 'overdue':
        return 'error'
      default:
        return 'default'
    }
  }

  const handleCreateProgram = () => {
    const newProg: TrainingProgram = {
      id: (programs.length + 1).toString(),
      title: newProgram.title,
      type: newProgram.type,
      status: 'draft',
      duration: newProgram.duration,
      assignedUsers: 0,
      completionRate: 0,
      dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      instructor: 'Current User'
    }
    setPrograms([newProg, ...programs])
    setCreateDialogOpen(false)
    setNewProgram({ title: '', type: 'GMP', duration: '', description: '' })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const trainingStats = {
    totalPrograms: programs.length,
    activePrograms: programs.filter(p => p.status === 'active').length,
    totalAssignments: assignments.length,
    completedAssignments: assignments.filter(a => a.status === 'completed').length,
    overdue: assignments.filter(a => a.status === 'overdue').length,
    avgCompletion: Math.round(programs.reduce((acc, p) => acc + p.completionRate, 0) / programs.length) || 0
  }

  return (
    <Container sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
            <School color="primary" />
            Training Management (TMS)
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Training Management System for employee development and compliance
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => window.location.reload()}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Program
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
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
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                    {trainingStats.totalPrograms}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Training Programs
                  </Typography>
                </Box>
                <School sx={{ fontSize: 40, color: 'primary.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                    {trainingStats.completedAssignments}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Completed
                  </Typography>
                </Box>
                <CheckCircle sx={{ fontSize: 40, color: 'success.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'error.main' }}>
                    {trainingStats.overdue}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Overdue
                  </Typography>
                </Box>
                <Warning sx={{ fontSize: 40, color: 'error.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'info.main' }}>
                    {trainingStats.avgCompletion}%
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Avg Completion
                  </Typography>
                </Box>
                <Assignment sx={{ fontSize: 40, color: 'info.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tab Navigation */}
      <Box sx={{ mb: 3 }}>
        <Button
          variant={activeTab === 'programs' ? 'contained' : 'outlined'}
          onClick={() => setActiveTab('programs')}
          sx={{ mr: 2 }}
        >
          Training Programs
        </Button>
        <Button
          variant={activeTab === 'assignments' ? 'contained' : 'outlined'}
          onClick={() => setActiveTab('assignments')}
        >
          Assignments
        </Button>
      </Box>

      {/* Training Programs Table */}
      {activeTab === 'programs' && (
        <Paper sx={{ width: '100%', overflow: 'hidden' }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Program Title</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Assigned Users</TableCell>
                  <TableCell>Completion Rate</TableCell>
                  <TableCell>Instructor</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8}>
                      <LinearProgress />
                    </TableCell>
                  </TableRow>
                ) : (
                  programs.map((program) => (
                    <TableRow key={program.id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                          {program.title}
                        </Typography>
                      </TableCell>
                      <TableCell>{program.type}</TableCell>
                      <TableCell>
                        <Chip
                          label={program.status.charAt(0).toUpperCase() + program.status.slice(1)}
                          color={getStatusColor(program.status) as any}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{program.duration}</TableCell>
                      <TableCell>{program.assignedUsers}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={program.completionRate}
                            sx={{ width: 60, height: 6 }}
                          />
                          <Typography variant="caption">
                            {program.completionRate}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{program.instructor}</TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Program">
                          <IconButton size="small" onClick={() => alert(`View program: ${program.title}`)}>
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit Program">
                          <IconButton size="small" onClick={() => alert(`Edit program: ${program.title}`)}>
                            <Edit />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Start Training">
                          <IconButton size="small" onClick={() => alert(`Start training: ${program.title}`)}>
                            <PlayArrow />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Training Assignments Table */}
      {activeTab === 'assignments' && (
        <Paper sx={{ width: '100%', overflow: 'hidden' }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Program</TableCell>
                  <TableCell>Assignee</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Due Date</TableCell>
                  <TableCell>Completed Date</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={7}>
                      <LinearProgress />
                    </TableCell>
                  </TableRow>
                ) : (
                  assignments.map((assignment) => (
                    <TableRow key={assignment.id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                          {assignment.programTitle}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ width: 24, height: 24, fontSize: '0.875rem' }}>
                            {assignment.assignee.split(' ').map(n => n[0]).join('')}
                          </Avatar>
                          {assignment.assignee}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={assignment.status.replace('_', ' ').toUpperCase()}
                          color={getAssignmentStatusColor(assignment.status) as any}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={assignment.progress}
                            sx={{ width: 60, height: 6 }}
                          />
                          <Typography variant="caption">
                            {assignment.progress}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{formatDate(assignment.dueDate)}</TableCell>
                      <TableCell>
                        {assignment.completedDate ? formatDate(assignment.completedDate) : '-'}
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Assignment">
                          <IconButton size="small" onClick={() => alert(`View assignment for: ${assignment.assignee}`)}>
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Create Program Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Training Program</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Program Title"
              value={newProgram.title}
              onChange={(e) => setNewProgram({ ...newProgram, title: e.target.value })}
              margin="normal"
              required
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Training Type</InputLabel>
              <Select
                value={newProgram.type}
                onChange={(e) => setNewProgram({ ...newProgram, type: e.target.value })}
                label="Training Type"
              >
                <MenuItem value="GMP">Good Manufacturing Practices</MenuItem>
                <MenuItem value="Quality Control">Quality Control</MenuItem>
                <MenuItem value="Safety">Safety Training</MenuItem>
                <MenuItem value="Technical">Technical Training</MenuItem>
                <MenuItem value="Compliance">Compliance Training</MenuItem>
                <MenuItem value="Leadership">Leadership Development</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Duration"
              value={newProgram.duration}
              onChange={(e) => setNewProgram({ ...newProgram, duration: e.target.value })}
              margin="normal"
              placeholder="e.g., 4 hours, 2 days"
            />
            <TextField
              fullWidth
              label="Description"
              value={newProgram.description}
              onChange={(e) => setNewProgram({ ...newProgram, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateProgram} 
            variant="contained"
            disabled={!newProgram.title}
          >
            Create Program
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default TrainingPage