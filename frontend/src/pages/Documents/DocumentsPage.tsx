import React, { useEffect } from 'react'
import { Box, Typography, Button, Paper, Grid, Chip } from '@mui/material'
import { Add, Description } from '@mui/icons-material'
import { useDispatch } from 'react-redux'
import { setPageTitle, setBreadcrumbs } from '@store/slices/uiSlice'

const DocumentsPage: React.FC = () => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(setPageTitle('Document Management'))
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Documents' }
    ]))
  }, [dispatch])

  // Mock document data for testing
  const mockDocuments = [
    { id: 'DOC-001', title: 'SOP-Quality Control', type: 'SOP', status: 'Approved', version: '2.1', lastModified: '2024-01-15' },
    { id: 'DOC-002', title: 'WI-Sampling Procedure', type: 'Work Instruction', status: 'Draft', version: '1.0', lastModified: '2024-01-10' },
    { id: 'DOC-003', title: 'FORM-Batch Record', type: 'Form', status: 'Under Review', version: '3.2', lastModified: '2024-01-08' },
    { id: 'DOC-004', title: 'POLICY-Change Control', type: 'Policy', status: 'Approved', version: '1.5', lastModified: '2024-01-05' },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Approved': return 'success'
      case 'Draft': return 'warning'
      case 'Under Review': return 'info'
      case 'Rejected': return 'error'
      default: return 'default'
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Document Management (EDMS)
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
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
            <Typography variant="h4" sx={{ fontWeight: 600 }}>1,247</Typography>
            <Typography variant="body2">Total Documents</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'success.main', color: 'white' }}>
            <Typography variant="h4" sx={{ fontWeight: 600 }}>1,198</Typography>
            <Typography variant="body2">Approved</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'warning.main', color: 'white' }}>
            <Typography variant="h4" sx={{ fontWeight: 600 }}>23</Typography>
            <Typography variant="body2">Pending Review</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'error.main', color: 'white' }}>
            <Typography variant="h4" sx={{ fontWeight: 600 }}>26</Typography>
            <Typography variant="body2">Expired/Rejected</Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Document List */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Recent Documents
        </Typography>
        <Box sx={{ mt: 2 }}>
          {mockDocuments.map((doc) => (
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
                  {doc.id} • {doc.type} • Version {doc.version} • Modified: {doc.lastModified}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Chip 
                  label={doc.status} 
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
        
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Button variant="outlined" sx={{ minWidth: 200 }}>
            View All Documents ({mockDocuments.length + 1243} total)
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}

export default DocumentsPage