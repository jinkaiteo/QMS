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
  Tab,
  Tabs,
} from '@mui/material'
import {
  Add,
  Visibility,
  Edit,
  Warning,
  Assessment,
  Assignment,
  CheckCircle,
  Schedule,
  Error,
  Refresh,
  BugReport,
  Security,
} from '@mui/icons-material'

interface QualityEvent {
  id: string
  title: string
  type: 'deviation' | 'complaint' | 'incident' | 'audit_finding'
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'open' | 'investigation' | 'capa_required' | 'closed'
  reportedBy: string
  reportedDate: string
  dueDate: string
  assignedTo: string
}

interface CAPA {
  id: string
  title: string
  relatedEvent: string
  type: 'corrective' | 'preventive' | 'both'
  status: 'planning' | 'implementation' | 'verification' | 'completed'
  priority: 'low' | 'medium' | 'high'
  assignedTo: string
  dueDate: string
  progress: number
}

const QualityPage: React.FC = () => {
  const [qualityEvents, setQualityEvents] = useState<QualityEvent[]>([])
  const [capas, setCAPAs] = useState<CAPA[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createEventDialogOpen, setCreateEventDialogOpen] = useState(false)
  const [createCAPADialogOpen, setCreateCAPADialogOpen] = useState(false)
  const [activeTab, setActiveTab] = useState(0)
  const [newEvent, setNewEvent] = useState({
    title: '',
    type: 'deviation' as const,
    severity: 'medium' as const,
    description: '',
  })
  const [newCAPA, setNewCAPA] = useState({
    title: '',
    type: 'corrective' as const,
    priority: 'medium' as const,
    description: '',
  })

  // Mock quality data
  const mockQualityEvents: QualityEvent[] = [
    {
      id: '1',
      title: 'Temperature Deviation in Storage Area B',
      type: 'deviation',
      severity: 'high',
      status: 'investigation',
      reportedBy: 'John Smith',
      reportedDate: '2024-10-29T08:30:00Z',
      dueDate: '2024-11-05T17:00:00Z',
      assignedTo: 'Quality Team Lead'
    },
    {
      id: '2',
      title: 'Customer Complaint - Product Discoloration',
      type: 'complaint',
      severity: 'medium',
      status: 'capa_required',
      reportedBy: 'Customer Service',
      reportedDate: '2024-10-28T14:15:00Z',
      dueDate: '2024-11-10T17:00:00Z',
      assignedTo: 'Quality Manager'
    },
    {
      id: '3',
      title: 'Equipment Malfunction - Tablet Press #3',
      type: 'incident',
      severity: 'critical',
      status: 'open',
      reportedBy: 'Production Operator',
      reportedDate: '2024-10-30T10:45:00Z',
      dueDate: '2024-11-02T17:00:00Z',
      assignedTo: 'Maintenance Team'
    },
    {
      id: '4',
      title: 'GMP Audit Finding - Documentation Gap',
      type: 'audit_finding',
      severity: 'medium',
      status: 'closed',
      reportedBy: 'Internal Auditor',
      reportedDate: '2024-10-25T09:00:00Z',
      dueDate: '2024-11-01T17:00:00Z',
      assignedTo: 'Quality Assurance'
    }
  ]

  const mockCAPAs: CAPA[] = [
    {
      id: '1',
      title: 'Improve Temperature Monitoring System',
      relatedEvent: 'Temperature Deviation in Storage Area B',
      type: 'both',
      status: 'implementation',
      priority: 'high',
      assignedTo: 'Engineering Team',
      dueDate: '2024-11-15T17:00:00Z',
      progress: 65
    },
    {
      id: '2',
      title: 'Update Manufacturing Process Documentation',
      relatedEvent: 'GMP Audit Finding - Documentation Gap',
      type: 'corrective',
      status: 'completed',
      priority: 'medium',
      assignedTo: 'Quality Assurance',
      dueDate: '2024-11-01T17:00:00Z',
      progress: 100
    },
    {
      id: '3',
      title: 'Implement Preventive Maintenance Schedule',
      relatedEvent: 'Equipment Malfunction - Tablet Press #3',
      type: 'preventive',
      status: 'planning',
      priority: 'high',
      assignedTo: 'Maintenance Team',
      dueDate: '2024-11-20T17:00:00Z',
      progress: 25
    }
  ]

  useEffect(() => {
    const fetchQualityData = async () => {
      try {
        setLoading(true)
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        setQualityEvents(mockQualityEvents)
        setCAPAs(mockCAPAs)
        setError(null)
      } catch (err) {
        setError('Failed to load quality data')
      } finally {
        setLoading(false)
      }
    }

    fetchQualityData()
  }, [])

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error'
      case 'high':
        return 'warning'
      case 'medium':
        return 'info'
      case 'low':
        return 'success'
      default:
        return 'default'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'closed':
        return 'success'
      case 'implementation':
      case 'investigation':
        return 'info'
      case 'planning':
      case 'capa_required':
        return 'warning'
      case 'open':
        return 'error'
      default:
        return 'default'
    }
  }

  const handleCreateEvent = () => {
    const newQEvent: QualityEvent = {
      id: (qualityEvents.length + 1).toString(),
      title: newEvent.title,
      type: newEvent.type,
      severity: newEvent.severity,
      status: 'open',
      reportedBy: 'Current User',
      reportedDate: new Date().toISOString(),
      dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      assignedTo: 'Quality Team'
    }
    setQualityEvents([newQEvent, ...qualityEvents])
    setCreateEventDialogOpen(false)
    setNewEvent({ title: '', type: 'deviation', severity: 'medium', description: '' })
  }

  const handleCreateCAPA = () => {
    const newCAPAItem: CAPA = {
      id: (capas.length + 1).toString(),
      title: newCAPA.title,
      relatedEvent: 'General Investigation',
      type: newCAPA.type,
      status: 'planning',
      priority: newCAPA.priority,
      assignedTo: 'Quality Team',
      dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
      progress: 0
    }
    setCAPAs([newCAPAItem, ...capas])
    setCreateCAPADialogOpen(false)
    setNewCAPA({ title: '', type: 'corrective', priority: 'medium', description: '' })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const qualityStats = {
    totalEvents: qualityEvents.length,
    openEvents: qualityEvents.filter(e => e.status === 'open').length,
    criticalEvents: qualityEvents.filter(e => e.severity === 'critical').length,
    totalCAPAs: capas.length,
    activeCAPAs: capas.filter(c => c.status !== 'completed').length,
    completedCAPAs: capas.filter(c => c.status === 'completed').length,
  }

  return (
    <Container sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Warning color="primary" />
            Quality Management (QRM)
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Quality Risk Management for compliance and quality assurance
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
            onClick={() => setCreateEventDialogOpen(true)}
          >
            Report Event
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
                    {qualityStats.totalEvents}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Quality Events
                  </Typography>
                </Box>
                <BugReport sx={{ fontSize: 40, color: 'primary.main', opacity: 0.7 }} />
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
                    {qualityStats.openEvents}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Open Events
                  </Typography>
                </Box>
                <Error sx={{ fontSize: 40, color: 'error.main', opacity: 0.7 }} />
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
                    {qualityStats.completedCAPAs}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Completed CAPAs
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
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
                    {qualityStats.activeCAPAs}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Active CAPAs
                  </Typography>
                </Box>
                <Assignment sx={{ fontSize: 40, color: 'warning.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tab Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Quality Events" />
          <Tab label="CAPA Management" />
        </Tabs>
      </Box>

      {/* Quality Events Table */}
      {activeTab === 0 && (
        <Paper sx={{ width: '100%', overflow: 'hidden' }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Event Title</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Reported By</TableCell>
                  <TableCell>Reported Date</TableCell>
                  <TableCell>Due Date</TableCell>
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
                  qualityEvents.map((event) => (
                    <TableRow key={event.id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                          {event.title}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={event.type.replace('_', ' ').toUpperCase()}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={event.severity.toUpperCase()}
                          color={getSeverityColor(event.severity) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={event.status.replace('_', ' ').toUpperCase()}
                          color={getStatusColor(event.status) as any}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{event.reportedBy}</TableCell>
                      <TableCell>{formatDate(event.reportedDate)}</TableCell>
                      <TableCell>{formatDate(event.dueDate)}</TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Event">
                          <IconButton size="small" onClick={() => alert(`View event: ${event.title}`)}>
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit Event">
                          <IconButton size="small" onClick={() => alert(`Edit event: ${event.title}`)}>
                            <Edit />
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

      {/* CAPA Management Table */}
      {activeTab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">CAPA (Corrective and Preventive Actions)</Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateCAPADialogOpen(true)}
            >
              Create CAPA
            </Button>
          </Box>
          <Paper sx={{ width: '100%', overflow: 'hidden' }}>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>CAPA Title</TableCell>
                    <TableCell>Related Event</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Assigned To</TableCell>
                    <TableCell>Due Date</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={9}>
                        <LinearProgress />
                      </TableCell>
                    </TableRow>
                  ) : (
                    capas.map((capa) => (
                      <TableRow key={capa.id} hover>
                        <TableCell>
                          <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                            {capa.title}
                          </Typography>
                        </TableCell>
                        <TableCell>{capa.relatedEvent}</TableCell>
                        <TableCell>
                          <Chip
                            label={capa.type.toUpperCase()}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={capa.priority.toUpperCase()}
                            color={getSeverityColor(capa.priority) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={capa.status.replace('_', ' ').toUpperCase()}
                            color={getStatusColor(capa.status) as any}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={capa.progress}
                              sx={{ width: 60, height: 6 }}
                            />
                            <Typography variant="caption">
                              {capa.progress}%
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>{capa.assignedTo}</TableCell>
                        <TableCell>{formatDate(capa.dueDate)}</TableCell>
                        <TableCell align="center">
                          <Tooltip title="View CAPA">
                            <IconButton size="small" onClick={() => alert(`View CAPA: ${capa.title}`)}>
                              <Visibility />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit CAPA">
                            <IconButton size="small" onClick={() => alert(`Edit CAPA: ${capa.title}`)}>
                              <Edit />
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
        </Box>
      )}

      {/* Create Event Dialog */}
      <Dialog open={createEventDialogOpen} onClose={() => setCreateEventDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Report Quality Event</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Event Title"
              value={newEvent.title}
              onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
              margin="normal"
              required
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Event Type</InputLabel>
              <Select
                value={newEvent.type}
                onChange={(e) => setNewEvent({ ...newEvent, type: e.target.value as any })}
                label="Event Type"
              >
                <MenuItem value="deviation">Deviation</MenuItem>
                <MenuItem value="complaint">Customer Complaint</MenuItem>
                <MenuItem value="incident">Incident</MenuItem>
                <MenuItem value="audit_finding">Audit Finding</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Severity</InputLabel>
              <Select
                value={newEvent.severity}
                onChange={(e) => setNewEvent({ ...newEvent, severity: e.target.value as any })}
                label="Severity"
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Description"
              value={newEvent.description}
              onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateEventDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateEvent} 
            variant="contained"
            disabled={!newEvent.title}
          >
            Report Event
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create CAPA Dialog */}
      <Dialog open={createCAPADialogOpen} onClose={() => setCreateCAPADialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create CAPA</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="CAPA Title"
              value={newCAPA.title}
              onChange={(e) => setNewCAPA({ ...newCAPA, title: e.target.value })}
              margin="normal"
              required
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>CAPA Type</InputLabel>
              <Select
                value={newCAPA.type}
                onChange={(e) => setNewCAPA({ ...newCAPA, type: e.target.value as any })}
                label="CAPA Type"
              >
                <MenuItem value="corrective">Corrective Action</MenuItem>
                <MenuItem value="preventive">Preventive Action</MenuItem>
                <MenuItem value="both">Both</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Priority</InputLabel>
              <Select
                value={newCAPA.priority}
                onChange={(e) => setNewCAPA({ ...newCAPA, priority: e.target.value as any })}
                label="Priority"
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Description"
              value={newCAPA.description}
              onChange={(e) => setNewCAPA({ ...newCAPA, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateCAPADialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateCAPA} 
            variant="contained"
            disabled={!newCAPA.title}
          >
            Create CAPA
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default QualityPage