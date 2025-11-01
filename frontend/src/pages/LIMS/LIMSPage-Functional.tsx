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
  Science,
  Biotech,
  Assessment,
  Schedule,
  CheckCircle,
  Warning,
  Refresh,
  PlayArrow,
  Stop,
} from '@mui/icons-material'

interface Sample {
  id: string
  sampleId: string
  productName: string
  batchNumber: string
  sampleType: 'raw_material' | 'in_process' | 'finished_product' | 'stability'
  status: 'received' | 'testing' | 'completed' | 'failed' | 'on_hold'
  receivedDate: string
  dueDate: string
  assignedTo: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
}

interface TestMethod {
  id: string
  methodName: string
  testType: 'identity' | 'assay' | 'impurity' | 'dissolution' | 'microbiology'
  status: 'active' | 'under_review' | 'retired'
  version: string
  duration: string
  lastUpdated: string
}

interface TestResult {
  id: string
  sampleId: string
  testMethod: string
  result: string
  specification: string
  status: 'pass' | 'fail' | 'oos' | 'pending'
  analyst: string
  testDate: string
  reviewDate?: string
}

const LIMSPage: React.FC = () => {
  const [samples, setSamples] = useState<Sample[]>([])
  const [testMethods, setTestMethods] = useState<TestMethod[]>([])
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createSampleDialogOpen, setCreateSampleDialogOpen] = useState(false)
  const [activeTab, setActiveTab] = useState(0)
  const [newSample, setNewSample] = useState({
    sampleId: '',
    productName: '',
    batchNumber: '',
    sampleType: 'finished_product' as const,
    priority: 'medium' as const,
  })

  // Mock LIMS data
  const mockSamples: Sample[] = [
    {
      id: '1',
      sampleId: 'S-2024-001',
      productName: 'Aspirin Tablets 325mg',
      batchNumber: 'ASP240001',
      sampleType: 'finished_product',
      status: 'testing',
      receivedDate: '2024-10-28T09:00:00Z',
      dueDate: '2024-11-04T17:00:00Z',
      assignedTo: 'Lab Analyst A',
      priority: 'high'
    },
    {
      id: '2',
      sampleId: 'S-2024-002',
      productName: 'API - Acetaminophen',
      batchNumber: 'ACE240015',
      sampleType: 'raw_material',
      status: 'completed',
      receivedDate: '2024-10-25T14:30:00Z',
      dueDate: '2024-11-01T17:00:00Z',
      assignedTo: 'Lab Analyst B',
      priority: 'medium'
    },
    {
      id: '3',
      sampleId: 'S-2024-003',
      productName: 'Ibuprofen Capsules 200mg',
      batchNumber: 'IBU240008',
      sampleType: 'stability',
      status: 'received',
      receivedDate: '2024-10-30T11:15:00Z',
      dueDate: '2024-11-15T17:00:00Z',
      assignedTo: 'Stability Lab',
      priority: 'low'
    },
    {
      id: '4',
      sampleId: 'S-2024-004',
      productName: 'Gelatin Capsules',
      batchNumber: 'GEL240003',
      sampleType: 'in_process',
      status: 'failed',
      receivedDate: '2024-10-29T16:45:00Z',
      dueDate: '2024-11-05T17:00:00Z',
      assignedTo: 'QC Supervisor',
      priority: 'urgent'
    }
  ]

  const mockTestMethods: TestMethod[] = [
    {
      id: '1',
      methodName: 'HPLC Assay for Aspirin',
      testType: 'assay',
      status: 'active',
      version: '3.2',
      duration: '4 hours',
      lastUpdated: '2024-09-15T10:00:00Z'
    },
    {
      id: '2',
      methodName: 'Dissolution Test - USP Method',
      testType: 'dissolution',
      status: 'active',
      version: '2.1',
      duration: '6 hours',
      lastUpdated: '2024-08-20T14:30:00Z'
    },
    {
      id: '3',
      methodName: 'Microbial Limit Test',
      testType: 'microbiology',
      status: 'active',
      version: '1.5',
      duration: '72 hours',
      lastUpdated: '2024-10-01T09:15:00Z'
    },
    {
      id: '4',
      methodName: 'Related Substances by HPLC',
      testType: 'impurity',
      status: 'under_review',
      version: '4.0',
      duration: '5 hours',
      lastUpdated: '2024-10-25T11:30:00Z'
    }
  ]

  const mockTestResults: TestResult[] = [
    {
      id: '1',
      sampleId: 'S-2024-001',
      testMethod: 'HPLC Assay for Aspirin',
      result: '98.5%',
      specification: '95.0 - 105.0%',
      status: 'pass',
      analyst: 'Dr. Sarah Johnson',
      testDate: '2024-10-29T14:00:00Z',
      reviewDate: '2024-10-30T09:00:00Z'
    },
    {
      id: '2',
      sampleId: 'S-2024-002',
      testMethod: 'Identity Test - IR',
      result: 'Positive',
      specification: 'Positive',
      status: 'pass',
      analyst: 'Michael Chen',
      testDate: '2024-10-26T10:30:00Z',
      reviewDate: '2024-10-26T16:00:00Z'
    },
    {
      id: '3',
      sampleId: 'S-2024-004',
      testMethod: 'Dissolution Test',
      result: '45% at 30 min',
      specification: 'NLT 80% at 30 min',
      status: 'fail',
      analyst: 'Emma Rodriguez',
      testDate: '2024-10-30T13:15:00Z'
    }
  ]

  useEffect(() => {
    const fetchLIMSData = async () => {
      try {
        setLoading(true)
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        setSamples(mockSamples)
        setTestMethods(mockTestMethods)
        setTestResults(mockTestResults)
        setError(null)
      } catch (err) {
        setError('Failed to load LIMS data')
      } finally {
        setLoading(false)
      }
    }

    fetchLIMSData()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'pass':
      case 'active':
        return 'success'
      case 'testing':
      case 'pending':
      case 'under_review':
        return 'info'
      case 'received':
        return 'warning'
      case 'failed':
      case 'fail':
      case 'oos':
        return 'error'
      case 'on_hold':
      case 'retired':
        return 'default'
      default:
        return 'default'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
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

  const handleCreateSample = () => {
    const newSamp: Sample = {
      id: (samples.length + 1).toString(),
      sampleId: newSample.sampleId,
      productName: newSample.productName,
      batchNumber: newSample.batchNumber,
      sampleType: newSample.sampleType,
      status: 'received',
      receivedDate: new Date().toISOString(),
      dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      assignedTo: 'Lab Team',
      priority: newSample.priority
    }
    setSamples([newSamp, ...samples])
    setCreateSampleDialogOpen(false)
    setNewSample({ sampleId: '', productName: '', batchNumber: '', sampleType: 'finished_product', priority: 'medium' })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString() + ' ' + 
           new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const limsStats = {
    totalSamples: samples.length,
    activeSamples: samples.filter(s => s.status === 'testing').length,
    completedSamples: samples.filter(s => s.status === 'completed').length,
    failedSamples: samples.filter(s => s.status === 'failed').length,
    activeMethods: testMethods.filter(m => m.status === 'active').length,
    totalMethods: testMethods.length,
  }

  return (
    <Container sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Science color="primary" />
            Laboratory (LIMS)
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Laboratory Information Management System for sample tracking and testing
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
            onClick={() => setCreateSampleDialogOpen(true)}
          >
            Register Sample
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
                    {limsStats.totalSamples}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Total Samples
                  </Typography>
                </Box>
                <Biotech sx={{ fontSize: 40, color: 'primary.main', opacity: 0.7 }} />
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
                    {limsStats.activeSamples}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    In Testing
                  </Typography>
                </Box>
                <PlayArrow sx={{ fontSize: 40, color: 'info.main', opacity: 0.7 }} />
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
                    {limsStats.completedSamples}
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
                    {limsStats.failedSamples}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Failed
                  </Typography>
                </Box>
                <Warning sx={{ fontSize: 40, color: 'error.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tab Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Sample Management" />
          <Tab label="Test Methods" />
          <Tab label="Test Results" />
        </Tabs>
      </Box>

      {/* Sample Management Table */}
      {activeTab === 0 && (
        <Paper sx={{ width: '100%', overflow: 'hidden' }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Sample ID</TableCell>
                  <TableCell>Product Name</TableCell>
                  <TableCell>Batch Number</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Received Date</TableCell>
                  <TableCell>Due Date</TableCell>
                  <TableCell>Assigned To</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={10}>
                      <LinearProgress />
                    </TableCell>
                  </TableRow>
                ) : (
                  samples.map((sample) => (
                    <TableRow key={sample.id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                          {sample.sampleId}
                        </Typography>
                      </TableCell>
                      <TableCell>{sample.productName}</TableCell>
                      <TableCell>{sample.batchNumber}</TableCell>
                      <TableCell>
                        <Chip
                          label={sample.sampleType.replace('_', ' ').toUpperCase()}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={sample.status.replace('_', ' ').toUpperCase()}
                          color={getStatusColor(sample.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={sample.priority.toUpperCase()}
                          color={getPriorityColor(sample.priority) as any}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{formatDate(sample.receivedDate)}</TableCell>
                      <TableCell>{formatDate(sample.dueDate)}</TableCell>
                      <TableCell>{sample.assignedTo}</TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Sample">
                          <IconButton size="small" onClick={() => alert(`View sample: ${sample.sampleId}`)}>
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit Sample">
                          <IconButton size="small" onClick={() => alert(`Edit sample: ${sample.sampleId}`)}>
                            <Edit />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Start Testing">
                          <IconButton size="small" onClick={() => alert(`Start testing: ${sample.sampleId}`)}>
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

      {/* Test Methods Table */}
      {activeTab === 1 && (
        <Paper sx={{ width: '100%', overflow: 'hidden' }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Method Name</TableCell>
                  <TableCell>Test Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Version</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Last Updated</TableCell>
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
                  testMethods.map((method) => (
                    <TableRow key={method.id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                          {method.methodName}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={method.testType.replace('_', ' ').toUpperCase()}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={method.status.replace('_', ' ').toUpperCase()}
                          color={getStatusColor(method.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{method.version}</TableCell>
                      <TableCell>{method.duration}</TableCell>
                      <TableCell>{formatDate(method.lastUpdated)}</TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Method">
                          <IconButton size="small" onClick={() => alert(`View method: ${method.methodName}`)}>
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit Method">
                          <IconButton size="small" onClick={() => alert(`Edit method: ${method.methodName}`)}>
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

      {/* Test Results Table */}
      {activeTab === 2 && (
        <Paper sx={{ width: '100%', overflow: 'hidden' }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Sample ID</TableCell>
                  <TableCell>Test Method</TableCell>
                  <TableCell>Result</TableCell>
                  <TableCell>Specification</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Analyst</TableCell>
                  <TableCell>Test Date</TableCell>
                  <TableCell>Review Date</TableCell>
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
                  testResults.map((result) => (
                    <TableRow key={result.id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                          {result.sampleId}
                        </Typography>
                      </TableCell>
                      <TableCell>{result.testMethod}</TableCell>
                      <TableCell>{result.result}</TableCell>
                      <TableCell>{result.specification}</TableCell>
                      <TableCell>
                        <Chip
                          label={result.status.toUpperCase()}
                          color={getStatusColor(result.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{result.analyst}</TableCell>
                      <TableCell>{formatDate(result.testDate)}</TableCell>
                      <TableCell>
                        {result.reviewDate ? formatDate(result.reviewDate) : '-'}
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Result">
                          <IconButton size="small" onClick={() => alert(`View result: ${result.sampleId}`)}>
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit Result">
                          <IconButton size="small" onClick={() => alert(`Edit result: ${result.sampleId}`)}>
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

      {/* Create Sample Dialog */}
      <Dialog open={createSampleDialogOpen} onClose={() => setCreateSampleDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Register New Sample</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Sample ID"
              value={newSample.sampleId}
              onChange={(e) => setNewSample({ ...newSample, sampleId: e.target.value })}
              margin="normal"
              required
              placeholder="S-2024-XXX"
            />
            <TextField
              fullWidth
              label="Product Name"
              value={newSample.productName}
              onChange={(e) => setNewSample({ ...newSample, productName: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Batch Number"
              value={newSample.batchNumber}
              onChange={(e) => setNewSample({ ...newSample, batchNumber: e.target.value })}
              margin="normal"
              required
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Sample Type</InputLabel>
              <Select
                value={newSample.sampleType}
                onChange={(e) => setNewSample({ ...newSample, sampleType: e.target.value as any })}
                label="Sample Type"
              >
                <MenuItem value="raw_material">Raw Material</MenuItem>
                <MenuItem value="in_process">In-Process</MenuItem>
                <MenuItem value="finished_product">Finished Product</MenuItem>
                <MenuItem value="stability">Stability</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Priority</InputLabel>
              <Select
                value={newSample.priority}
                onChange={(e) => setNewSample({ ...newSample, priority: e.target.value as any })}
                label="Priority"
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateSampleDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateSample} 
            variant="contained"
            disabled={!newSample.sampleId || !newSample.productName || !newSample.batchNumber}
          >
            Register Sample
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default LIMSPage