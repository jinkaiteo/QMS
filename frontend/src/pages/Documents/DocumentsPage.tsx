import React, { useEffect, useState } from 'react'
import { Box, Typography, Button, Paper, Grid, Chip, CircularProgress, Alert } from '@mui/material'
import { Add, Description, Refresh } from '@mui/icons-material'
import { useDispatch } from 'react-redux'
import { setPageTitle, setBreadcrumbs } from '@store/slices/uiSlice'
import { documentsService, Document, DocumentSearchResponse } from '../../services/documentsService'

const DocumentsPage: React.FC = () => {
  const dispatch = useDispatch()
  const [documents, setDocuments] = useState<Document[]>([])
  const [stats, setStats] = useState({
    total: 0,
    approved: 0,
    pending_review: 0,
    draft: 0,
    expired: 0
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    dispatch(setPageTitle('Document Management'))
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Documents' }
    ]))
    
    loadDocuments()
    loadStats()
  }, [dispatch])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      setError(null)
      const response: DocumentSearchResponse = await documentsService.getDocuments(1, 10)
      setDocuments(response.items)
    } catch (err) {
      console.error('Error loading documents:', err)
      setError(documentsService.handleError(err))
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const statsResponse = await documentsService.getDocumentStats()
      setStats(statsResponse)
    } catch (err) {
      console.error('Error loading document stats:', err)
      // Don't set error for stats, as documents are more important
    }
  }

  const handleRefresh = () => {
    loadDocuments()
    loadStats()
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved': return 'success'
      case 'draft': return 'warning'
      case 'under_review': 
      case 'under review':
      case 'pending_review': return 'info'
      case 'rejected': 
      case 'retired': return 'error'
      default: return 'default'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const formatStatus = (status: string) => {
    return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Document Management (EDMS)
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button 
            variant="outlined" 
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button variant="outlined" startIcon={<Description />}>
            Import Documents
          </Button>
          <Button variant="contained" startIcon={<Add />}>
            Create Document
          </Button>
        </Box>
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'primary.main', color: 'white' }}>
            <Typography variant="h4" sx={{ fontWeight: 600 }}>{stats.total}</Typography>
            <Typography variant="body2">Total Documents</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'success.main', color: 'white' }}>
            <Typography variant="h4" sx={{ fontWeight: 600 }}>{stats.approved}</Typography>
            <Typography variant="body2">Approved</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'warning.main', color: 'white' }}>
            <Typography variant="h4" sx={{ fontWeight: 600 }}>{stats.pending_review}</Typography>
            <Typography variant="body2">Pending Review</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'error.main', color: 'white' }}>
            <Typography variant="h4" sx={{ fontWeight: 600 }}>{stats.draft + stats.expired}</Typography>
            <Typography variant="body2">Draft/Expired</Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Document List */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Recent Documents {loading && <CircularProgress size={20} sx={{ ml: 2 }} />}
        </Typography>
        
        {loading && documents.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : documents.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="textSecondary">
              No documents found. {error ? 'Please check your connection and try again.' : 'Create your first document to get started.'}
            </Typography>
          </Box>
        ) : (
          <Box sx={{ mt: 2 }}>
            {documents.map((doc) => (
              <Paper 
                key={doc.id}
                sx={{ 
                  p: 2, 
                  mb: 2, 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  '&:hover': { bgcolor: 'action.hover', cursor: 'pointer' }
                }}
              >
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {doc.title}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {doc.document_number} • {doc.document_type.name} • Version {doc.current_version} • Modified: {formatDate(doc.updated_at)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
                    Author: {doc.author.full_name} • Created: {formatDate(doc.created_at)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Chip 
                    label={formatStatus(doc.status)} 
                    color={getStatusColor(doc.status) as any}
                    size="small"
                  />
                  <Button size="small" variant="outlined">
                    View
                  </Button>
                </Box>
              </Paper>
            ))}
          </Box>
        )}
        
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Button variant="outlined" sx={{ minWidth: 200 }}>
            View All Documents ({stats.total} total)
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}

export default DocumentsPage