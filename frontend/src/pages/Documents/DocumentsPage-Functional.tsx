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
} from '@mui/material'
import {
  Add,
  Visibility,
  Edit,
  Download,
  Upload,
  Description,
  Assignment,
  CheckCircle,
  Schedule,
  Warning,
  Refresh,
} from '@mui/icons-material'

interface Document {
  id: string
  title: string
  type: string
  status: 'draft' | 'review' | 'approved' | 'expired'
  version: string
  author: string
  lastModified: string
  size: string
}

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newDocument, setNewDocument] = useState({
    title: '',
    type: 'SOP',
    description: '',
  })

  // Mock document data with pharmaceutical-specific content
  const mockDocuments: Document[] = [
    {
      id: '1',
      title: 'Standard Operating Procedure - Batch Record Review',
      type: 'SOP',
      status: 'approved',
      version: '2.1',
      author: 'Dr. Sarah Johnson',
      lastModified: '2024-10-28T10:30:00Z',
      size: '245 KB'
    },
    {
      id: '2',
      title: 'Quality Manual - Manufacturing Standards',
      type: 'Quality Manual',
      status: 'review',
      version: '1.3',
      author: 'Michael Chen',
      lastModified: '2024-10-29T14:15:00Z',
      size: '1.2 MB'
    },
    {
      id: '3',
      title: 'Validation Protocol - HVAC System',
      type: 'Validation',
      status: 'draft',
      version: '1.0',
      author: 'Emma Rodriguez',
      lastModified: '2024-10-30T09:45:00Z',
      size: '567 KB'
    },
    {
      id: '4',
      title: 'Change Control - Equipment Upgrade',
      type: 'Change Control',
      status: 'approved',
      version: '1.2',
      author: 'James Wilson',
      lastModified: '2024-10-25T16:20:00Z',
      size: '892 KB'
    },
    {
      id: '5',
      title: 'Training Record - GMP Guidelines',
      type: 'Training',
      status: 'approved',
      version: '3.0',
      author: 'Lisa Thompson',
      lastModified: '2024-10-27T11:10:00Z',
      size: '324 KB'
    }
  ]

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true)
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        setDocuments(mockDocuments)
        setError(null)
      } catch (err) {
        setError('Failed to load documents')
      } finally {
        setLoading(false)
      }
    }

    fetchDocuments()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'success'
      case 'review':
        return 'warning'
      case 'draft':
        return 'info'
      case 'expired':
        return 'error'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle sx={{ fontSize: 16 }} />
      case 'review':
        return <Schedule sx={{ fontSize: 16 }} />
      case 'draft':
        return <Edit sx={{ fontSize: 16 }} />
      case 'expired':
        return <Warning sx={{ fontSize: 16 }} />
      default:
        return null
    }
  }

  const handleCreateDocument = () => {
    const newDoc: Document = {
      id: (documents.length + 1).toString(),
      title: newDocument.title,
      type: newDocument.type,
      status: 'draft',
      version: '1.0',
      author: 'Current User',
      lastModified: new Date().toISOString(),
      size: '0 KB'
    }
    setDocuments([newDoc, ...documents])
    setCreateDialogOpen(false)
    setNewDocument({ title: '', type: 'SOP', description: '' })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString() + ' ' + 
           new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const documentStats = {
    total: documents.length,
    approved: documents.filter(d => d.status === 'approved').length,
    review: documents.filter(d => d.status === 'review').length,
    draft: documents.filter(d => d.status === 'draft').length,
  }

  return (
    <Container sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Description color="primary" />
            Document Management (EDMS)
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Electronic Document Management System for pharmaceutical documentation
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
            Create Document
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
                    {documentStats.total}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Total Documents
                  </Typography>
                </Box>
                <Assignment sx={{ fontSize: 40, color: 'primary.main', opacity: 0.7 }} />
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
                    {documentStats.approved}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Approved
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
                    {documentStats.review}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    In Review
                  </Typography>
                </Box>
                <Schedule sx={{ fontSize: 40, color: 'warning.main', opacity: 0.7 }} />
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
                    {documentStats.draft}
                  </Typography>
                  <Typography variant="subtitle2" color="textSecondary">
                    Drafts
                  </Typography>
                </Box>
                <Edit sx={{ fontSize: 40, color: 'info.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Documents Table */}
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Document Title</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Version</TableCell>
                <TableCell>Author</TableCell>
                <TableCell>Last Modified</TableCell>
                <TableCell>Size</TableCell>
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
                documents.map((doc) => (
                  <TableRow key={doc.id} hover>
                    <TableCell>
                      <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                        {doc.title}
                      </Typography>
                    </TableCell>
                    <TableCell>{doc.type}</TableCell>
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(doc.status)}
                        label={doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                        color={getStatusColor(doc.status) as any}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{doc.version}</TableCell>
                    <TableCell>{doc.author}</TableCell>
                    <TableCell>{formatDate(doc.lastModified)}</TableCell>
                    <TableCell>{doc.size}</TableCell>
                    <TableCell align="center">
                      <Tooltip title="View Document">
                        <IconButton size="small" onClick={() => alert(`View document: ${doc.title}`)}>
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit Document">
                        <IconButton size="small" onClick={() => alert(`Edit document: ${doc.title}`)}>
                          <Edit />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Download">
                        <IconButton size="small" onClick={() => alert(`Download document: ${doc.title}`)}>
                          <Download />
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

      {/* Create Document Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Document</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Document Title"
              value={newDocument.title}
              onChange={(e) => setNewDocument({ ...newDocument, title: e.target.value })}
              margin="normal"
              required
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Document Type</InputLabel>
              <Select
                value={newDocument.type}
                onChange={(e) => setNewDocument({ ...newDocument, type: e.target.value })}
                label="Document Type"
              >
                <MenuItem value="SOP">Standard Operating Procedure</MenuItem>
                <MenuItem value="Quality Manual">Quality Manual</MenuItem>
                <MenuItem value="Validation">Validation Protocol</MenuItem>
                <MenuItem value="Change Control">Change Control</MenuItem>
                <MenuItem value="Training">Training Document</MenuItem>
                <MenuItem value="Policy">Policy Document</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Description"
              value={newDocument.description}
              onChange={(e) => setNewDocument({ ...newDocument, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateDocument} 
            variant="contained"
            disabled={!newDocument.title}
          >
            Create Document
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default DocumentsPage