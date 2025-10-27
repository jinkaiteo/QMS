import React, { useEffect, useState } from 'react'
import { 
  Box, Typography, Paper, Grid, Button, Card, CardContent, 
  LinearProgress, Chip, Avatar, List, ListItem, ListItemText,
  ListItemAvatar, Tabs, Tab, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, FormControl, InputLabel, Select,
  MenuItem, Autocomplete, FormControlLabel, Checkbox, Alert, 
  Divider, Table, TableBody, TableCell, TableRow, CircularProgress
} from '@mui/material'
import { 
  School, Add, Assignment, CheckCircle, Schedule, 
  TrendingUp, BookmarkBorder, PlayArrow, Close,
  Verified, Security, History, Badge
} from '@mui/icons-material'
import { useDispatch, useSelector } from 'react-redux'
import { setPageTitle, setBreadcrumbs } from '@store/slices/uiSlice'
import { addNotification } from '@store/slices/uiSlice'
import { useNavigate, useLocation } from 'react-router-dom'
import { trainingService, TrainingProgram, TrainingAssignment } from '@services/trainingService'
import { RootState } from '@store/store'

const TrainingPage: React.FC = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const location = useLocation()
  // const { user } = useSelector((state: RootState) => state.auth)  // Will be used for permissions
  
  const [tabValue, setTabValue] = useState(0)
  const [createProgramOpen, setCreateProgramOpen] = useState(false)
  const [assignTrainingOpen, setAssignTrainingOpen] = useState(false)
  const [trainingViewerOpen, setTrainingViewerOpen] = useState(false)
  const [selectedTraining, setSelectedTraining] = useState<TrainingAssignment | null>(null)
  const [programDetailsOpen, setProgramDetailsOpen] = useState(false)
  const [selectedProgram, setSelectedProgram] = useState<TrainingProgram | null>(null)
  const [eSignatureOpen, setESignatureOpen] = useState(false)
  const [currentModule, setCurrentModule] = useState(0)
  
  // API Data State
  const [programs, setPrograms] = useState<TrainingProgram[]>([])
  const [myAssignments, setMyAssignments] = useState<TrainingAssignment[]>([])
  const [dashboardStats, setDashboardStats] = useState({
    totalPrograms: 0,
    activeAssignments: 0,
    completedThisMonth: 0,
    overdueTrainings: 0,
    complianceRate: 0
  })
  const [employees, setEmployees] = useState<Array<{
    id: string
    name: string
    email: string
    department: string
    jobRole: string
  }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Set initial tab based on URL
  useEffect(() => {
    const path = location.pathname
    if (path === '/training/programs') {
      setTabValue(1)
    } else if (path === '/training/assignments') {
      setTabValue(2)
    } else {
      setTabValue(0) // Default to My Training
    }
  }, [location.pathname])

  useEffect(() => {
    dispatch(setPageTitle('Training Records Management'))
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Training' }
    ]))
    
    // Load initial data
    loadInitialData()
  }, [dispatch])

  // Load initial data from API
  const loadInitialData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Load data in parallel
      const [
        programsData,
        assignmentsData,
        statsData,
        employeesData
      ] = await Promise.all([
        trainingService.getPrograms(),
        trainingService.getMyAssignments(),
        trainingService.getDashboardStats(),
        trainingService.getEmployees()
      ])
      
      setPrograms(programsData)
      setMyAssignments(assignmentsData)
      setDashboardStats(statsData)
      setEmployees(employeesData)
      
    } catch (err) {
      const errorMessage = trainingService.handleError(err)
      setError(errorMessage)
      dispatch(addNotification({
        type: 'error',
        title: 'Loading Error',
        message: `Failed to load training data: ${errorMessage}`
      }))
    } finally {
      setLoading(false)
    }
  }

  // Form state for creating programs
  const [programForm, setProgramForm] = useState({
    title: '',
    description: '',
    type: '',
    duration: '',
    passingScore: '70',
    validityPeriod: '12',
    linkedDocuments: [],
    requireApproval: true,
    sendReminders: false,
    autoAttachDocuments: false
  })

  // Form state for assigning training
  const [assignmentForm, setAssignmentForm] = useState<{
    programId: string
    employeeIds: Array<{id: string; name: string; email: string; department: string; jobRole: string}>
    dueDate: string
    notes: string
    notifyEmployees: boolean
    notifyManagers: boolean
  }>({
    programId: '',
    employeeIds: [],
    dueDate: '',
    notes: '',
    notifyEmployees: true,
    notifyManagers: false
  })

  // Handle program creation
  const handleCreateProgram = async () => {
    try {
      if (!programForm.title || !programForm.type || !programForm.duration) {
        dispatch(addNotification({
          type: 'error',
          title: 'Validation Error',
          message: 'Please fill in all required fields'
        }))
        return
      }

      setLoading(true)
      const newProgram = await trainingService.createProgram({
        title: programForm.title,
        description: programForm.description,
        type: programForm.type,
        duration: parseInt(programForm.duration),
        passingScore: parseInt(programForm.passingScore),
        validityPeriod: parseInt(programForm.validityPeriod),
        linkedDocuments: programForm.linkedDocuments.map((doc: any) => doc.id),
        modules: [] // Will be added in later phases
      })

      setPrograms([...programs, newProgram])
      setCreateProgramOpen(false)
      setProgramForm({
        title: '',
        description: '',
        type: '',
        duration: '',
        passingScore: '70',
        validityPeriod: '12',
        linkedDocuments: [],
        requireApproval: true,
        sendReminders: false,
        autoAttachDocuments: false
      })

      dispatch(addNotification({
        type: 'success',
        title: 'Success',
        message: 'Training program created successfully'
      }))
    } catch (err) {
      const errorMessage = trainingService.handleError(err)
      dispatch(addNotification({
        type: 'error',
        title: 'Creation Error',
        message: `Failed to create program: ${errorMessage}`
      }))
    } finally {
      setLoading(false)
    }
  }

  // Handle training assignment
  const handleAssignTraining = async () => {
    try {
      if (!assignmentForm.programId || assignmentForm.employeeIds.length === 0 || !assignmentForm.dueDate) {
        dispatch(addNotification({
          type: 'error',
          title: 'Validation Error',
          message: 'Please fill in all required fields'
        }))
        return
      }

      setLoading(true)
      await trainingService.assignTraining({
        programId: assignmentForm.programId,
        employeeIds: assignmentForm.employeeIds.map(emp => emp.id),
        dueDate: assignmentForm.dueDate,
        notes: assignmentForm.notes,
        notifyEmployees: assignmentForm.notifyEmployees,
        notifyManagers: assignmentForm.notifyManagers
      })

      // Refresh assignments
      const updatedAssignments = await trainingService.getMyAssignments()
      setMyAssignments(updatedAssignments)

      setAssignTrainingOpen(false)
      setAssignmentForm({
        programId: '',
        employeeIds: [],
        dueDate: '',
        notes: '',
        notifyEmployees: true,
        notifyManagers: false
      })

      dispatch(addNotification({
        type: 'success',
        title: 'Assignment Complete',
        message: `Training assigned to ${assignmentForm.employeeIds.length} employee(s)`
      }))
    } catch (err) {
      const errorMessage = trainingService.handleError(err)
      dispatch(addNotification({
        type: 'error',
        title: 'Assignment Error',
        message: `Failed to assign training: ${errorMessage}`
      }))
    } finally {
      setLoading(false)
    }
  }

  // Handle tab changes and URL navigation
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
    switch (newValue) {
      case 0:
        navigate('/training')
        break
      case 1:
        navigate('/training/programs')
        break
      case 2:
        navigate('/training/assignments')
        break
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'in_progress': return 'info'
      case 'assigned': return 'warning'
      case 'overdue': return 'error'
      default: return 'default'
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading training data...</Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>Error Loading Training Data</Typography>
          <Typography>{error}</Typography>
          <Button variant="outlined" onClick={loadInitialData} sx={{ mt: 2 }}>
            Retry
          </Button>
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Training Records Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button 
            variant="outlined" 
            startIcon={<Assignment />}
            onClick={() => setAssignTrainingOpen(true)}
            disabled={loading}
          >
            Assign Training
          </Button>
          <Button 
            variant="contained" 
            startIcon={<Add />}
            onClick={() => setCreateProgramOpen(true)}
            disabled={loading}
          >
            Create Program
          </Button>
        </Box>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ bgcolor: 'primary.main', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <School sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 600 }}>{dashboardStats.totalPrograms}</Typography>
              <Typography variant="body2">Training Programs</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ bgcolor: 'info.main', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Assignment sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 600 }}>{dashboardStats.activeAssignments}</Typography>
              <Typography variant="body2">Active Assignments</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ bgcolor: 'success.main', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <CheckCircle sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 600 }}>{dashboardStats.completedThisMonth}</Typography>
              <Typography variant="body2">Completed This Month</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ bgcolor: 'warning.main', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Schedule sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 600 }}>{dashboardStats.overdueTrainings}</Typography>
              <Typography variant="body2">Overdue Trainings</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ bgcolor: 'success.main', color: 'white' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUp sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 600 }}>{dashboardStats.complianceRate}%</Typography>
              <Typography variant="body2">Compliance Rate</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content with Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="My Training" />
          <Tab label="Training Programs" />
          <Tab label="Training Management" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                My Training Assignments
              </Typography>
              <List>
                {myAssignments.map((training) => (
                  <ListItem key={training.id} sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: training.status === 'completed' ? 'success.main' : 'primary.main' }}>
                        {training.status === 'completed' ? <CheckCircle /> : <BookmarkBorder />}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={programs.find(p => p.id === training.programId)?.title || 'Unknown Program'}
                      secondary={
                        <React.Fragment>
                          <Typography component="span" variant="body2" color="textSecondary" display="block">
                            Due: {training.dueDate}
                          </Typography>
                          <Box component="span" sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={training.progress} 
                              sx={{ flexGrow: 1, mr: 2 }}
                            />
                            <Typography component="span" variant="body2">{training.progress}%</Typography>
                          </Box>
                        </React.Fragment>
                      }
                    />
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
                      <Chip 
                        label={training.status} 
                        color={getStatusColor(training.status) as any}
                        size="small"
                      />
                      {training.status !== 'completed' && (
                        <Button 
                          size="small" 
                          startIcon={<PlayArrow />}
                          onClick={() => {
                            setSelectedTraining(training)
                            setTrainingViewerOpen(true)
                          }}
                        >
                          {training.status === 'assigned' ? 'Start' : 'Continue'}
                        </Button>
                      )}
                    </Box>
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button variant="outlined" fullWidth startIcon={<Assignment />}>
                  View All My Training
                </Button>
                <Button variant="outlined" fullWidth startIcon={<History />}>
                  Training Records & Transcript
                </Button>
                <Button variant="outlined" fullWidth startIcon={<Badge />}>
                  Certification Status
                </Button>
                <Button variant="outlined" fullWidth startIcon={<Schedule />}>
                  Training Calendar
                </Button>
                <Button variant="outlined" fullWidth startIcon={<Assignment />}>
                  View Training History
                </Button>
                <Button variant="outlined" fullWidth startIcon={<TrendingUp />}>
                  My Progress Report
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {tabValue === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Available Training Programs
          </Typography>
          <Grid container spacing={2}>
            {programs.map((program) => (
              <Grid item xs={12} sm={6} md={4} key={program.id}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {program.title}
                      </Typography>
                      <Chip 
                        label={program.status} 
                        color={program.status === 'active' ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Type: {program.type}
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Duration: {program.duration}
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Status: {program.status}
                    </Typography>
                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      <Button 
                        size="small" 
                        variant="outlined"
                        onClick={() => {
                          setSelectedProgram(program)
                          setProgramDetailsOpen(true)
                        }}
                      >
                        View Details
                      </Button>
                      <Button size="small" variant="contained">
                        Enroll
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Training Management Tab */}
      {tabValue === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Training Management</Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Quick Actions</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Button variant="outlined" fullWidth startIcon={<Add />}>
                      Create New Training Program
                    </Button>
                    <Button variant="outlined" fullWidth startIcon={<Assignment />}>
                      Assign Training to Employees
                    </Button>
                    <Button variant="outlined" fullWidth startIcon={<Schedule />}>
                      Schedule Training Sessions
                    </Button>
                    <Button variant="outlined" fullWidth startIcon={<TrendingUp />}>
                      View Training Progress
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Recent Activity</Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="GMP Training Completed" 
                        secondary="John Doe - 2 hours ago" 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="New Program Created" 
                        secondary="Data Integrity Training - Yesterday" 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Training Assigned" 
                        secondary="Safety Training to 15 employees - 2 days ago" 
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          
          <Alert severity="info" sx={{ mt: 3 }}>
            <Typography variant="body2">
              <strong>Phase 1 Implementation:</strong> This simplified training management focuses on core functionality. 
              Additional compliance features will be added in future phases.
            </Typography>
          </Alert>
        </Paper>
      )}

      {/* Create Program Modal */}
      <Dialog open={createProgramOpen} onClose={() => setCreateProgramOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Create Training Program
          <Button onClick={() => setCreateProgramOpen(false)}>
            <Close />
          </Button>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
            <TextField
              label="Program Title"
              fullWidth
              placeholder="e.g., GMP Fundamentals"
              required
              value={programForm.title}
              onChange={(e) => setProgramForm({ ...programForm, title: e.target.value })}
            />
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Training Type</InputLabel>
                  <Select 
                    label="Training Type" 
                    value={programForm.type}
                    onChange={(e) => setProgramForm({ ...programForm, type: e.target.value })}
                  >
                    <MenuItem value="mandatory">Mandatory</MenuItem>
                    <MenuItem value="compliance">Compliance</MenuItem>
                    <MenuItem value="safety">Safety</MenuItem>
                    <MenuItem value="technical">Technical</MenuItem>
                    <MenuItem value="leadership">Leadership</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Duration (hours)"
                  type="number"
                  fullWidth
                  placeholder="4"
                  value={programForm.duration}
                  onChange={(e) => setProgramForm({ ...programForm, duration: e.target.value })}
                />
              </Grid>
            </Grid>
            <TextField
              label="Description"
              multiline
              rows={3}
              fullWidth
              placeholder="Detailed description of the training program objectives and content..."
              value={programForm.description}
              onChange={(e) => setProgramForm({ ...programForm, description: e.target.value })}
            />
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Passing Score (%)"
                  type="number"
                  fullWidth
                  value={programForm.passingScore}
                  onChange={(e) => setProgramForm({ ...programForm, passingScore: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Validity Period (months)"
                  type="number"
                  fullWidth
                  value={programForm.validityPeriod}
                  onChange={(e) => setProgramForm({ ...programForm, validityPeriod: e.target.value })}
                />
              </Grid>
            </Grid>
            {/* EDMS Document Linking */}
            <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
              Linked Documents (EDMS)
            </Typography>
            <Autocomplete
              multiple
              options={[
                { id: 'SOP-001', title: 'SOP-Quality Control Procedures', type: 'SOP', category: 'Reference Material' },
                { id: 'WI-002', title: 'WI-Sampling Procedure', type: 'Work Instruction', category: 'Reference Material' },
                { id: 'FORM-003', title: 'Training Assessment Form', type: 'Form', category: 'Training Form' },
                { id: 'FORM-004', title: 'Skills Checklist Template', type: 'Form', category: 'Training Form' },
                { id: 'POLICY-001', title: 'GMP Policy Document', type: 'Policy', category: 'Reference Material' },
                { id: 'MANUAL-001', title: 'Equipment Operation Manual', type: 'Manual', category: 'Reference Material' },
                { id: 'CERT-001', title: 'Certification Template', type: 'Certificate', category: 'Certificate Template' }
              ]}
              getOptionLabel={(option) => `${option.id} - ${option.title}`}
              renderInput={(params) => (
                <TextField 
                  {...params} 
                  label="Select Documents" 
                  placeholder="Search EDMS documents..."
                  helperText="Link reference materials, training forms, certificates, and other relevant documents"
                />
              )}
              renderOption={(props, option) => (
                <Box component="li" {...props}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {option.id} - {option.title}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                      <Chip label={option.type} size="small" variant="outlined" />
                      <Chip 
                        label={option.category} 
                        size="small" 
                        color={
                          option.category === 'Training Form' ? 'primary' :
                          option.category === 'Reference Material' ? 'info' :
                          option.category === 'Certificate Template' ? 'success' : 'default'
                        }
                      />
                    </Box>
                  </Box>
                </Box>
              )}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip
                    {...getTagProps({ index })}
                    key={option.id}
                    label={`${option.id} - ${option.type}`}
                    size="small"
                    color={
                      option.category === 'Training Form' ? 'primary' :
                      option.category === 'Reference Material' ? 'info' :
                      option.category === 'Certificate Template' ? 'success' : 'default'
                    }
                  />
                ))
              }
            />
            
            {/* Document Category Quick Filters */}
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Document Categories:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip 
                  icon={<Assignment />} 
                  label="Reference Materials" 
                  size="small" 
                  variant="outlined" 
                  color="info"
                  clickable
                />
                <Chip 
                  icon={<Assignment />} 
                  label="Training Forms" 
                  size="small" 
                  variant="outlined" 
                  color="primary"
                  clickable
                />
                <Chip 
                  icon={<CheckCircle />} 
                  label="Certificate Templates" 
                  size="small" 
                  variant="outlined" 
                  color="success"
                  clickable
                />
                <Button size="small" sx={{ minHeight: 'auto', py: 0.5 }}>
                  Browse EDMS →
                </Button>
              </Box>
            </Box>

            <FormControlLabel
              control={<Checkbox defaultChecked />}
              label="Require manager approval for completion"
            />
            <FormControlLabel
              control={<Checkbox />}
              label="Send reminder notifications"
            />
            <FormControlLabel
              control={<Checkbox />}
              label="Auto-attach linked documents to employee assignments"
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setCreateProgramOpen(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleCreateProgram}
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Program'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Assign Training Modal */}
      <Dialog open={assignTrainingOpen} onClose={() => setAssignTrainingOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Assign Training
          <Button onClick={() => setAssignTrainingOpen(false)}>
            <Close />
          </Button>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Select Training Program</InputLabel>
              <Select 
                label="Select Training Program" 
                value={assignmentForm.programId}
                onChange={(e) => setAssignmentForm({ ...assignmentForm, programId: e.target.value })}
              >
                {programs.map((program) => (
                  <MenuItem key={program.id} value={program.id}>
                    {program.title}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Autocomplete
              multiple
              options={employees}
              value={assignmentForm.employeeIds}
              onChange={(_, newValue) => {
                setAssignmentForm({ ...assignmentForm, employeeIds: newValue })
              }}
              getOptionLabel={(option) => `${option.name} (${option.department})`}
              renderInput={(params) => (
                <TextField {...params} label="Select Employees" placeholder="Search employees..." />
              )}
              renderOption={(props, option) => (
                <Box component="li" {...props}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{option.name}</Typography>
                    <Typography variant="caption" color="textSecondary">{option.department}</Typography>
                  </Box>
                </Box>
              )}
            />

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Assignment Date"
                  type="date"
                  fullWidth
                  value={new Date().toISOString().split('T')[0]}
                  InputLabelProps={{ shrink: true }}
                  disabled
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Due Date"
                  type="date"
                  fullWidth
                  value={assignmentForm.dueDate}
                  onChange={(e) => setAssignmentForm({ ...assignmentForm, dueDate: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
            </Grid>

            <TextField
              label="Assignment Notes"
              multiline
              rows={2}
              fullWidth
              placeholder="Optional notes or instructions for the assigned employees..."
              value={assignmentForm.notes}
              onChange={(e) => setAssignmentForm({ ...assignmentForm, notes: e.target.value })}
            />

            <FormControlLabel
              control={
                <Checkbox 
                  checked={assignmentForm.notifyEmployees}
                  onChange={(e) => setAssignmentForm({ ...assignmentForm, notifyEmployees: e.target.checked })}
                />
              }
              label="Send notification email to assigned employees"
            />
            <FormControlLabel
              control={
                <Checkbox 
                  checked={assignmentForm.notifyManagers}
                  onChange={(e) => setAssignmentForm({ ...assignmentForm, notifyManagers: e.target.checked })}
                />
              }
              label="Send notification to managers"
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setAssignTrainingOpen(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleAssignTraining}
            disabled={loading}
          >
            {loading ? 'Assigning...' : 'Assign Training'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Training Viewer Modal */}
      <Dialog 
        open={trainingViewerOpen} 
        onClose={() => setTrainingViewerOpen(false)} 
        maxWidth="lg" 
        fullWidth
        PaperProps={{ sx: { height: '90vh' } }}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: 1, borderColor: 'divider' }}>
          <Box>
            <Typography variant="h6">
              {selectedTraining ? programs.find(p => p.id === selectedTraining.programId)?.title || 'Training Program' : 'Training Program'}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Due: {selectedTraining?.dueDate} • Progress: {selectedTraining?.progress || 0}%
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              label={selectedTraining?.status} 
              color={getStatusColor(selectedTraining?.status) as any}
              size="small"
            />
            <Button onClick={() => setTrainingViewerOpen(false)}>
              <Close />
            </Button>
          </Box>
        </DialogTitle>
        
        <DialogContent sx={{ p: 0, display: 'flex', height: '100%' }}>
          {/* Sidebar Navigation */}
          <Paper sx={{ width: 280, borderRadius: 0, borderRight: 1, borderColor: 'divider' }}>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                Training Modules
              </Typography>
            </Box>
            <List dense>
              {[
                { id: 1, title: 'Introduction & Objectives', duration: '15 min', completed: true },
                { id: 2, title: 'Theoretical Overview', duration: '45 min', completed: true },
                { id: 3, title: 'Practical Examples', duration: '30 min', completed: selectedTraining?.progress >= 75 },
                { id: 4, title: 'Hands-on Exercise', duration: '25 min', completed: false },
                { id: 5, title: 'Assessment Quiz', duration: '20 min', completed: false },
                { id: 6, title: 'Final Evaluation', duration: '10 min', completed: false }
              ].map((module) => (
                <ListItem key={module.id} sx={{ py: 1 }}>
                  <ListItemAvatar>
                    <Avatar sx={{ 
                      width: 32, 
                      height: 32, 
                      bgcolor: module.completed ? 'success.main' : 'grey.300',
                      fontSize: '0.875rem'
                    }}>
                      {module.completed ? <CheckCircle /> : module.id}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Typography variant="body2" sx={{ fontWeight: module.completed ? 600 : 400 }}>
                        {module.title}
                      </Typography>
                    }
                    secondary={module.duration}
                  />
                </ListItem>
              ))}
            </List>
            
            {/* Linked Documents */}
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                Reference Materials
              </Typography>
              <List dense>
                <ListItem sx={{ py: 0.5 }}>
                  <ListItemText 
                    primary={
                      <Typography variant="body2" color="primary" sx={{ cursor: 'pointer' }}>
                        📄 SOP-Quality Control
                      </Typography>
                    }
                  />
                </ListItem>
                <ListItem sx={{ py: 0.5 }}>
                  <ListItemText 
                    primary={
                      <Typography variant="body2" color="primary" sx={{ cursor: 'pointer' }}>
                        📋 Assessment Form
                      </Typography>
                    }
                  />
                </ListItem>
              </List>
            </Box>
          </Paper>

          {/* Main Content Area */}
          <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
            {/* Progress Bar */}
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" color="textSecondary">
                  Overall Progress
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {selectedTraining?.progress || 0}% Complete
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={selectedTraining?.progress || 0} 
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>

            {/* Training Content */}
            <Box sx={{ flexGrow: 1, p: 3, overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                Module 3: Practical Examples
              </Typography>
              
              <Typography variant="body1" paragraph>
                In this module, you will learn practical applications of quality control procedures 
                in pharmaceutical manufacturing. This hands-on approach will help you understand 
                the real-world implementation of the concepts covered in the theoretical overview.
              </Typography>

              <Box sx={{ my: 3, p: 2, bgcolor: 'info.50', borderRadius: 1, border: 1, borderColor: 'info.200' }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'info.main', mb: 1 }}>
                  💡 Learning Objectives
                </Typography>
                <Typography variant="body2">
                  • Identify critical control points in the manufacturing process<br/>
                  • Apply sampling techniques for quality testing<br/>
                  • Interpret test results and make quality decisions<br/>
                  • Document findings according to GMP requirements
                </Typography>
              </Box>

              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Case Study: Batch Release Decision
              </Typography>
              
              <Typography variant="body1" paragraph>
                You are the QC analyst responsible for batch ABC-12345. Review the test results 
                below and determine whether this batch meets release specifications:
              </Typography>

              <Paper sx={{ p: 2, my: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Test Results:</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2">• Assay: 99.2% (Spec: 98.0-102.0%)</Typography>
                    <Typography variant="body2">• Impurity A: 0.08% (Spec: ≤0.1%)</Typography>
                    <Typography variant="body2">• Dissolution: 95% in 30 min (Spec: ≥80%)</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2">• pH: 6.8 (Spec: 6.5-7.5)</Typography>
                    <Typography variant="body2">• Water Content: 2.1% (Spec: ≤3.0%)</Typography>
                    <Typography variant="body2">• Uniformity: RSD 1.2% (Spec: ≤5.0%)</Typography>
                  </Grid>
                </Grid>
              </Paper>

              <Box sx={{ my: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Your Decision:
                </Typography>
                <FormControl component="fieldset">
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <FormControlLabel
                      control={<input type="radio" name="decision" value="release" />}
                      label="Release the batch - All specifications met"
                    />
                    <FormControlLabel
                      control={<input type="radio" name="decision" value="reject" />}
                      label="Reject the batch - Specifications not met"
                    />
                    <FormControlLabel
                      control={<input type="radio" name="decision" value="investigate" />}
                      label="Investigate further - Need additional testing"
                    />
                  </Box>
                </FormControl>
              </Box>
            </Box>

            {/* Navigation Controls */}
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between' }}>
              <Button variant="outlined" startIcon={<Assignment />}>
                ← Previous Module
              </Button>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant="outlined">
                  Save Progress
                </Button>
                <Button 
                  variant="contained" 
                  endIcon={<PlayArrow />}
                  onClick={() => {
                    // Simulate module completion
                    if (currentModule === 5) { // Last module
                      setESignatureOpen(true)
                    } else {
                      setCurrentModule(currentModule + 1)
                    }
                  }}
                >
                  {currentModule === 5 ? 'Complete Training' : 'Next Module →'}
                </Button>
              </Box>
            </Box>
          </Box>
        </DialogContent>
      </Dialog>

      {/* Program Details Modal */}
      <Dialog 
        open={programDetailsOpen} 
        onClose={() => setProgramDetailsOpen(false)} 
        maxWidth="lg" 
        fullWidth
        PaperProps={{ sx: { height: '90vh' } }}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: 1, borderColor: 'divider' }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              {selectedProgram?.title}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
              <Chip 
                label={selectedProgram?.type} 
                color="primary" 
                size="small"
              />
              <Chip 
                label={selectedProgram?.status} 
                color={selectedProgram?.status === 'active' ? 'success' : 'default'}
                size="small"
              />
              <Typography variant="body2" color="textSecondary">
                Duration: {selectedProgram?.duration}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button variant="contained" startIcon={<Assignment />}>
              Assign to Employees
            </Button>
            <Button onClick={() => setProgramDetailsOpen(false)}>
              <Close />
            </Button>
          </Box>
        </DialogTitle>
        
        <DialogContent sx={{ p: 0, display: 'flex', height: '100%' }}>
          {/* Left Panel - Program Info */}
          <Box sx={{ width: '60%', p: 3, overflow: 'auto' }}>
            {/* Program Overview */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Program Overview
              </Typography>
              <Typography variant="body1" paragraph>
                This comprehensive training program covers essential Good Manufacturing Practice (GMP) 
                principles for pharmaceutical manufacturing. Participants will learn fundamental concepts, 
                regulatory requirements, and practical applications of GMP in their daily work activities.
              </Typography>
              
              <Grid container spacing={3} sx={{ mt: 2 }}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Created By</Typography>
                  <Typography variant="body2">Dr. Sarah Johnson, QA Manager</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Last Updated</Typography>
                  <Typography variant="body2">January 15, 2024</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Passing Score</Typography>
                  <Typography variant="body2">80%</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">Validity Period</Typography>
                  <Typography variant="body2">12 months</Typography>
                </Grid>
              </Grid>
            </Paper>

            {/* Learning Objectives */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Learning Objectives
              </Typography>
              <List dense>
                {[
                  'Understand fundamental GMP principles and regulations',
                  'Identify critical control points in manufacturing processes',
                  'Apply proper documentation and record-keeping practices',
                  'Recognize and respond to quality deviations',
                  'Implement contamination control strategies',
                  'Demonstrate proper cleaning and sanitization procedures'
                ].map((objective, index) => (
                  <ListItem key={index} sx={{ pl: 0 }}>
                    <ListItemAvatar>
                      <Avatar sx={{ width: 24, height: 24, bgcolor: 'primary.main', fontSize: '0.75rem' }}>
                        {index + 1}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText primary={objective} />
                  </ListItem>
                ))}
              </List>
            </Paper>

            {/* Course Curriculum */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Course Curriculum
              </Typography>
              <List>
                {[
                  { module: 'Introduction to GMP', duration: '45 min', description: 'Overview of regulatory framework and basic principles' },
                  { module: 'Quality Management System', duration: '60 min', description: 'QMS components, documentation, and implementation' },
                  { module: 'Personnel & Training', duration: '30 min', description: 'Staff qualifications, hygiene, and training requirements' },
                  { module: 'Facilities & Equipment', duration: '50 min', description: 'Design, maintenance, and qualification requirements' },
                  { module: 'Documentation & Records', duration: '40 min', description: 'Record keeping, batch records, and data integrity' },
                  { module: 'Assessment & Certification', duration: '35 min', description: 'Final evaluation and certification process' }
                ].map((module, index) => (
                  <ListItem key={index} sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'info.main' }}>
                        {index + 1}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {module.module}
                          </Typography>
                          <Chip label={module.duration} size="small" variant="outlined" />
                        </Box>
                      }
                      secondary={module.description}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>

            {/* Linked Documents */}
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Reference Materials & Documents
              </Typography>
              <Grid container spacing={2}>
                {[
                  { id: 'SOP-001', title: 'GMP Manufacturing Procedures', type: 'SOP', category: 'Reference' },
                  { id: 'FORM-001', title: 'Training Assessment Form', type: 'Form', category: 'Assessment' },
                  { id: 'CERT-001', title: 'GMP Certification Template', type: 'Certificate', category: 'Certificate' },
                  { id: 'GUIDE-001', title: 'FDA GMP Guidelines', type: 'Guideline', category: 'Reference' }
                ].map((doc) => (
                  <Grid item xs={12} sm={6} key={doc.id}>
                    <Card sx={{ cursor: 'pointer', '&:hover': { elevation: 4 } }}>
                      <CardContent sx={{ p: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {doc.id}
                          </Typography>
                          <Chip 
                            label={doc.category} 
                            size="small" 
                            color={doc.category === 'Assessment' ? 'primary' : 'info'}
                          />
                        </Box>
                        <Typography variant="body2" color="textSecondary">
                          {doc.title}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {doc.type}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Box>

          {/* Right Panel - Enrollment & Analytics */}
          <Paper sx={{ width: '40%', borderRadius: 0, borderLeft: 1, borderColor: 'divider' }}>
            {/* Enrollment Statistics */}
            <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6" gutterBottom>
                Enrollment Statistics
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.50', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
                      {selectedProgram?.enrolled || 45}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Total Enrolled
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.50', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main' }}>
                      38
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Completed
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.50', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ fontWeight: 600, color: 'warning.main' }}>
                      5
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      In Progress
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'error.50', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ fontWeight: 600, color: 'error.main' }}>
                      2
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Overdue
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Completion Rate
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={84} 
                  sx={{ height: 8, borderRadius: 4 }}
                />
                <Typography variant="body2" sx={{ mt: 1, textAlign: 'right' }}>
                  84% Complete
                </Typography>
              </Box>
            </Box>

            {/* Enrolled Employees */}
            <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6" gutterBottom>
                Enrolled Employees
              </Typography>
              <List dense sx={{ maxHeight: 300, overflow: 'auto' }}>
                {[
                  { name: 'John Doe', department: 'Quality Control', status: 'Completed', progress: 100 },
                  { name: 'Jane Smith', department: 'Production', status: 'In Progress', progress: 65 },
                  { name: 'Mike Johnson', department: 'QA', status: 'Completed', progress: 100 },
                  { name: 'Sarah Wilson', department: 'R&D', status: 'In Progress', progress: 30 },
                  { name: 'David Brown', department: 'Regulatory', status: 'Overdue', progress: 15 }
                ].map((employee, index) => (
                  <ListItem key={index} sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}>
                    <ListItemAvatar>
                      <Avatar sx={{ width: 32, height: 32 }}>
                        {employee.name.split(' ').map(n => n[0]).join('')}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={employee.name}
                      secondary={
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            {employee.department}
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={employee.progress} 
                            sx={{ mt: 0.5, height: 4 }}
                          />
                        </Box>
                      }
                    />
                    <Chip 
                      label={employee.status} 
                      size="small"
                      color={getStatusColor(employee.status) as any}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>

            {/* Quick Actions */}
            <Box sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Program Management
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button variant="contained" fullWidth startIcon={<Assignment />}>
                  Assign to More Employees
                </Button>
                <Button variant="outlined" fullWidth>
                  Edit Program Content
                </Button>
                <Button variant="outlined" fullWidth>
                  Generate Report
                </Button>
                <Button variant="outlined" fullWidth>
                  Export Enrollment Data
                </Button>
                <Button variant="outlined" fullWidth>
                  Duplicate Program
                </Button>
              </Box>
            </Box>
          </Paper>
        </DialogContent>
      </Dialog>

      {/* Electronic Signature Modal (21 CFR Part 11 Compliance) */}
      <Dialog open={eSignatureOpen} onClose={() => setESignatureOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ bgcolor: 'primary.main', color: 'white', display: 'flex', alignItems: 'center', gap: 2 }}>
          <Security />
          <Typography variant="h6">Electronic Signature Required (21 CFR Part 11)</Typography>
        </DialogTitle>
        <DialogContent sx={{ mt: 3 }}>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              This training completion requires an electronic signature in compliance with 21 CFR Part 11. 
              Your signature confirms that you have completed all required modules and understand the training content.
            </Typography>
          </Alert>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>Training Completion Summary</Typography>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell><strong>Training Program:</strong></TableCell>
                  <TableCell>{selectedTraining?.title}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Employee:</strong></TableCell>
                  <TableCell>Test Admin (admin@test.com)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Completion Date:</strong></TableCell>
                  <TableCell>{new Date().toLocaleDateString()}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Training Duration:</strong></TableCell>
                  <TableCell>4.5 hours</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Assessment Score:</strong></TableCell>
                  <TableCell>95% (Pass - Required: 80%)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              label="Username"
              value="admin"
              disabled
              fullWidth
              helperText="Your authenticated username"
            />
            <TextField
              label="Password"
              type="password"
              fullWidth
              placeholder="Enter your password to confirm signature"
              required
            />
            <TextField
              label="Signature Meaning"
              multiline
              rows={2}
              fullWidth
              defaultValue="I confirm that I have completed this training program, understand the content, and will apply the knowledge in my work activities."
            />
            <FormControlLabel
              control={<Checkbox required />}
              label="I acknowledge that this electronic signature has the same legal effect as a handwritten signature"
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setESignatureOpen(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            startIcon={<Verified />}
            onClick={() => {
              // TODO: Process electronic signature
              setESignatureOpen(false)
              setTrainingViewerOpen(false)
              // Show success notification
            }}
          >
            Sign & Complete Training
          </Button>
        </DialogActions>
      </Dialog>

      {/* Note: Complex modals removed for Phase 1 simplicity */}
    </Box>
  )
}

export default TrainingPage