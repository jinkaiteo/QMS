import React, { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  DatePicker,
  TextField,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  GetApp,
  Visibility,
  PictureAsPdf,
  TableChart,
  TrendingUp,
  Assessment,
  BarChart,
  Timeline,
  Refresh,
  Schedule,
} from '@mui/icons-material'
import { LineChart, Line, BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

interface ReportTemplate {
  id: string
  name: string
  description: string
  type: 'compliance' | 'training' | 'quality' | 'documents' | 'lims'
  category: 'operational' | 'regulatory' | 'management'
  parameters: string[]
  lastGenerated?: string
  format: 'pdf' | 'excel' | 'both'
}

interface ReportData {
  title: string
  summary: any
  chartData: any[]
  tableData: any[]
  compliance: {
    score: number
    areas: any[]
  }
}

const AdvancedReporting: React.FC = () => {
  const [reportTemplates] = useState<ReportTemplate[]>([
    {
      id: '1',
      name: 'Training Compliance Report',
      description: 'Comprehensive training completion and compliance analysis',
      type: 'training',
      category: 'regulatory',
      parameters: ['date_range', 'department', 'training_type'],
      lastGenerated: '2024-10-30T14:30:00Z',
      format: 'both'
    },
    {
      id: '2',
      name: 'Quality Events Summary',
      description: 'Analysis of quality events, trends, and CAPA effectiveness',
      type: 'quality',
      category: 'operational',
      parameters: ['date_range', 'severity', 'status'],
      lastGenerated: '2024-10-29T16:45:00Z',
      format: 'pdf'
    },
    {
      id: '3',
      name: 'Document Management Report',
      description: 'Document lifecycle, approval rates, and compliance status',
      type: 'documents',
      category: 'regulatory',
      parameters: ['date_range', 'document_type', 'status'],
      lastGenerated: '2024-10-28T10:15:00Z',
      format: 'excel'
    },
    {
      id: '4',
      name: 'Laboratory Testing Report',
      description: 'Sample testing performance, turnaround times, and results analysis',
      type: 'lims',
      category: 'operational',
      parameters: ['date_range', 'sample_type', 'test_method'],
      lastGenerated: '2024-10-30T09:20:00Z',
      format: 'both'
    },
    {
      id: '5',
      name: 'Executive Dashboard Report',
      description: 'High-level KPIs and compliance metrics for executive review',
      type: 'compliance',
      category: 'management',
      parameters: ['date_range', 'module'],
      lastGenerated: '2024-10-30T17:00:00Z',
      format: 'pdf'
    }
  ])

  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null)
  const [generatingReport, setGeneratingReport] = useState(false)
  const [reportPreviewOpen, setReportPreviewOpen] = useState(false)
  const [previewData, setPreviewData] = useState<ReportData | null>(null)
  const [reportParameters, setReportParameters] = useState<any>({})

  // Mock chart data
  const mockChartData = [
    { month: 'Jan', training: 85, quality: 12, documents: 45 },
    { month: 'Feb', training: 88, quality: 8, documents: 52 },
    { month: 'Mar', training: 92, quality: 15, documents: 38 },
    { month: 'Apr', training: 89, quality: 6, documents: 41 },
    { month: 'May', training: 94, quality: 9, documents: 47 },
    { month: 'Jun', training: 91, quality: 11, documents: 44 },
  ]

  const complianceData = [
    { name: 'Training', value: 94, color: '#4caf50' },
    { name: 'Documents', value: 87, color: '#2196f3' },
    { name: 'Quality', value: 92, color: '#ff9800' },
    { name: 'LIMS', value: 89, color: '#9c27b0' },
  ]

  const handleGenerateReport = async (template: ReportTemplate, format: 'pdf' | 'excel' | 'preview') => {
    setGeneratingReport(true)
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      if (format === 'preview') {
        // Show preview
        setPreviewData({
          title: template.name,
          summary: {
            totalRecords: 1247,
            complianceScore: 91,
            lastUpdated: new Date().toISOString(),
            reportPeriod: '2024-Q3'
          },
          chartData: mockChartData,
          tableData: [
            { metric: 'Training Completion Rate', value: '94%', target: '95%', status: 'Good' },
            { metric: 'Document Approval Time', value: '3.2 days', target: '3 days', status: 'Attention' },
            { metric: 'Quality Events Closed', value: '89%', target: '90%', status: 'Good' },
            { metric: 'LIMS Turnaround Time', value: '2.1 days', target: '2 days', status: 'Excellent' },
          ],
          compliance: {
            score: 91,
            areas: complianceData
          }
        })
        setReportPreviewOpen(true)
      } else {
        // Simulate download
        const blob = new Blob(['Mock report content'], { 
          type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${template.name}.${format}`
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Report generation failed:', error)
    } finally {
      setGeneratingReport(false)
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'training':
        return 'primary'
      case 'quality':
        return 'warning'
      case 'documents':
        return 'info'
      case 'lims':
        return 'secondary'
      case 'compliance':
        return 'success'
      default:
        return 'default'
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'regulatory':
        return 'error'
      case 'operational':
        return 'info'
      case 'management':
        return 'success'
      default:
        return 'default'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString() + ' ' + 
           new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <Container sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Assessment color="primary" />
            Advanced Reporting & Analytics
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Generate comprehensive reports and analytics for all QMS modules
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={() => window.location.reload()}
        >
          Refresh
        </Button>
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                    {reportTemplates.length}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Report Templates
                  </Typography>
                </Box>
                <BarChart sx={{ fontSize: 40, color: 'primary.main', opacity: 0.7 }} />
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
                    91%
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Overall Compliance
                  </Typography>
                </Box>
                <TrendingUp sx={{ fontSize: 40, color: 'success.main', opacity: 0.7 }} />
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
                    247
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Reports Generated
                  </Typography>
                </Box>
                <Timeline sx={{ fontSize: 40, color: 'info.main', opacity: 0.7 }} />
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
                    12
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Scheduled Reports
                  </Typography>
                </Box>
                <Schedule sx={{ fontSize: 40, color: 'warning.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Compliance Overview Chart */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Compliance Trends (Last 6 Months)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mockChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="training" stroke="#4caf50" strokeWidth={2} />
                  <Line type="monotone" dataKey="quality" stroke="#ff9800" strokeWidth={2} />
                  <Line type="monotone" dataKey="documents" stroke="#2196f3" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Module Compliance Scores
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={complianceData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ name, value }) => `${name}: ${value}%`}
                  >
                    {complianceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Report Templates */}
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
        Available Report Templates
      </Typography>

      <Grid container spacing={3}>
        {reportTemplates.map((template) => (
          <Grid item xs={12} md={6} lg={4} key={template.id}>
            <Card 
              sx={{ 
                height: '100%',
                '&:hover': {
                  boxShadow: 4,
                  transform: 'translateY(-2px)',
                  transition: 'all 0.3s ease-in-out',
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {template.name}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Chip
                      label={template.type}
                      size="small"
                      color={getTypeColor(template.type) as any}
                      variant="outlined"
                    />
                    <Chip
                      label={template.category}
                      size="small"
                      color={getCategoryColor(template.category) as any}
                      variant="filled"
                    />
                  </Box>
                </Box>

                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  {template.description}
                </Typography>

                {template.lastGenerated && (
                  <Typography variant="caption" color="textSecondary" sx={{ mb: 2, display: 'block' }}>
                    Last generated: {formatDate(template.lastGenerated)}
                  </Typography>
                )}

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Tooltip title="Preview Report">
                      <IconButton 
                        size="small" 
                        onClick={() => handleGenerateReport(template, 'preview')}
                        disabled={generatingReport}
                      >
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Generate PDF">
                      <IconButton 
                        size="small" 
                        onClick={() => handleGenerateReport(template, 'pdf')}
                        disabled={generatingReport}
                      >
                        <PictureAsPdf />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Generate Excel">
                      <IconButton 
                        size="small" 
                        onClick={() => handleGenerateReport(template, 'excel')}
                        disabled={generatingReport}
                      >
                        <TableChart />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  
                  {generatingReport && (
                    <CircularProgress size={20} />
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Report Preview Dialog */}
      <Dialog 
        open={reportPreviewOpen} 
        onClose={() => setReportPreviewOpen(false)} 
        maxWidth="lg" 
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Report Preview</Typography>
            <Box>
              <Button startIcon={<PictureAsPdf />} sx={{ mr: 1 }}>
                Download PDF
              </Button>
              <Button startIcon={<TableChart />}>
                Download Excel
              </Button>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          {previewData && (
            <Box>
              {/* Report Summary */}
              <Typography variant="h6" gutterBottom>
                {previewData.title}
              </Typography>
              
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="textSecondary">Total Records</Typography>
                  <Typography variant="h6">{previewData.summary.totalRecords}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="textSecondary">Compliance Score</Typography>
                  <Typography variant="h6" color="success.main">{previewData.summary.complianceScore}%</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="textSecondary">Report Period</Typography>
                  <Typography variant="h6">{previewData.summary.reportPeriod}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="textSecondary">Last Updated</Typography>
                  <Typography variant="h6">{formatDate(previewData.summary.lastUpdated)}</Typography>
                </Grid>
              </Grid>

              {/* Sample Table */}
              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Key Metrics
              </Typography>
              <TableContainer component={Paper} sx={{ mb: 3 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Metric</TableCell>
                      <TableCell>Current Value</TableCell>
                      <TableCell>Target</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {previewData.tableData.map((row, index) => (
                      <TableRow key={index}>
                        <TableCell>{row.metric}</TableCell>
                        <TableCell>{row.value}</TableCell>
                        <TableCell>{row.target}</TableCell>
                        <TableCell>
                          <Chip 
                            label={row.status} 
                            size="small" 
                            color={row.status === 'Excellent' ? 'success' : row.status === 'Good' ? 'primary' : 'warning'}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReportPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default AdvancedReporting