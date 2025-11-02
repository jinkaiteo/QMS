import React, { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  Button,
  Chip,
  Grid,
  Divider,
  IconButton,
  Paper,
  Tab,
  Tabs,
  List,
  ListItem,
  ListItemText,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material'
import {
  Close,
  Download,
  Edit,
  Send,
  CheckCircle,
  Cancel,
  History,
  Link as LinkIcon
} from '@mui/icons-material'
import { Document, documentsService } from '../../services/documentsService'
import DocumentWorkflowPanel from './DocumentWorkflowPanel'
import DocumentUpload from './DocumentUpload'

interface DocumentDetailModalProps {
  document: Document | null
  open: boolean
  onClose: () => void
  currentUser?: any
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({
  document,
  open,
  onClose,
  currentUser
}) => {
  const [tabValue, setTabValue] = useState(0)
  const [reviewComment, setReviewComment] = useState('')
  const [approvalComment, setApprovalComment] = useState('')
  const [effectiveDate, setEffectiveDate] = useState('')
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)

  if (!document) return null

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved': return 'success'
      case 'draft': return 'warning'
      case 'under_review':
      case 'pending_review': return 'info'
      case 'rejected': return 'error'
      case 'effective': return 'success'
      default: return 'default'
    }
  }

  const formatStatus = (status: string) => {
    return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const canStartReview = () => {
    // Document must be in draft status, user must have review permissions, AND document must have a file attached
    const hasFile = document.file_path || document.current_version || document.versions?.length > 0
    return document.status === 'draft' && 
           currentUser?.permissions?.includes('review') && 
           hasFile
  }

  const canApprove = () => {
    return document.status === 'under_review' && currentUser?.permissions?.includes('approve')
  }

  const canEdit = () => {
    return ['draft'].includes(document.status) && 
           (currentUser?.id === document.author.id || currentUser?.permissions?.includes('write'))
  }

  const handleStartReview = async () => {
    try {
      // For now, assign to current user as reviewer (in real app, this would be a selection)
      const reviewerId = currentUser?.id || 1
      const dueDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] // 7 days from now
      
      await documentsService.startReviewWorkflow(document.id, reviewerId, dueDate)
      
      // Update document status to pending_review
      await documentsService.updateDocumentStatus(document.id, 'pending_review', 'Review workflow initiated')
      
      alert('Review workflow started successfully!')
      // Trigger parent component to refresh data
      onClose()
      window.location.reload() // Simple refresh for now
    } catch (error) {
      console.error('Error starting review:', error)
      alert('Failed to start review workflow: ' + documentsService.handleError(error))
    }
  }

  const handleSubmitReview = async (approved: boolean) => {
    try {
      if (!reviewComment.trim()) {
        alert('Please provide review comments')
        return
      }

      // For demo purposes, we'll use a mock workflow ID
      // In a real implementation, this would come from the document's current workflow
      const mockWorkflowId = 1
      
      await documentsService.submitReview(mockWorkflowId, approved, reviewComment)
      
      // Update document status based on review result
      const newStatus = approved ? 'pending_approval' : 'draft'
      const reason = approved ? 'Review approved, pending final approval' : 'Review rejected, returned to draft'
      
      await documentsService.updateDocumentStatus(document.id, newStatus, reason)
      
      alert(`Review ${approved ? 'approved' : 'rejected'} successfully!`)
      setReviewComment('')
      onClose()
      window.location.reload() // Simple refresh for now
    } catch (error) {
      console.error('Error submitting review:', error)
      alert('Failed to submit review: ' + documentsService.handleError(error))
    }
  }

  const handleSubmitApproval = async (approved: boolean) => {
    try {
      if (!approvalComment.trim()) {
        alert('Please provide approval comments')
        return
      }

      if (approved && !effectiveDate) {
        alert('Please provide an effective date for approval')
        return
      }

      // For demo purposes, we'll use a mock workflow ID
      const mockWorkflowId = 1
      
      await documentsService.submitApproval(mockWorkflowId, approved, approvalComment, effectiveDate)
      
      // Update document status based on approval result
      const newStatus = approved ? 'approved' : 'draft'
      const reason = approved ? 'Document approved and effective' : 'Document rejected, returned to draft'
      
      await documentsService.updateDocumentStatus(document.id, newStatus, reason)
      
      alert(`Document ${approved ? 'approved' : 'rejected'} successfully!`)
      setApprovalComment('')
      setEffectiveDate('')
      onClose()
      window.location.reload() // Simple refresh for now
    } catch (error) {
      console.error('Error submitting approval:', error)
      alert('Failed to submit approval: ' + documentsService.handleError(error))
    }
  }

  const handleDownload = (type: string) => {
    // TODO: Implement download functionality
    console.log('Download requested:', type)
    alert(`Download ${type} requested! (Implementation in Phase 2)`)
  }

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '80vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" component="div">
              {document.title}
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              {document.document_number} • Version {document.current_version || '1.0'}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              label={formatStatus(document.status)}
              color={getStatusColor(document.status) as any}
              size="medium"
            />
            <IconButton onClick={onClose}>
              <Close />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Details" />
          <Tab label="Workflow" />
          <Tab label="Versions" />
          <Tab label="Dependencies" />
        </Tabs>
      </Box>

      <DialogContent sx={{ p: 0 }}>
        {/* Details Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Document Information
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Document Number
                    </Typography>
                    <Typography variant="body1">{document.document_number}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Document Type
                    </Typography>
                    <Typography variant="body1">{document.document_type.name}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Author
                    </Typography>
                    <Typography variant="body1">{document.author.full_name}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Created Date
                    </Typography>
                    <Typography variant="body1">{formatDate(document.created_at)}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Last Modified
                    </Typography>
                    <Typography variant="body1">{formatDate(document.updated_at)}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Effective Date
                    </Typography>
                    <Typography variant="body1">
                      {document.effective_date ? formatDate(document.effective_date) : 'Not set'}
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>

              {/* Tags */}
              {document.tags && document.tags.length > 0 && (
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Tags
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {document.tags.map((tag, index) => (
                      <Chip key={index} label={tag} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Paper>
              )}
            </Grid>

            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Quick Actions
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {/* File Upload Section for documents without files */}
                  {document.status === 'draft' && !(document.file_path || document.current_version || document.versions?.length > 0) && (
                    <>
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<LinkIcon />}
                        fullWidth
                        onClick={() => setUploadDialogOpen(true)}
                      >
                        Upload Document File
                      </Button>
                      <Divider />
                    </>
                  )}
                  <Button
                    variant="outlined"
                    startIcon={<Download />}
                    onClick={() => handleDownload('original')}
                    fullWidth
                    disabled={!(document.file_path || document.current_version || document.versions?.length > 0)}
                  >
                    Download Original
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Download />}
                    onClick={() => handleDownload('annotated')}
                    fullWidth
                  >
                    Download Annotated
                  </Button>
                  {document.status === 'approved' && (
                    <Button
                      variant="contained"
                      startIcon={<Download />}
                      onClick={() => handleDownload('official_pdf')}
                      fullWidth
                    >
                      Download Official PDF
                    </Button>
                  )}
                  <Divider />
                  {canEdit() && (
                    <Button
                      variant="outlined"
                      startIcon={<Edit />}
                      fullWidth
                    >
                      Edit Document
                    </Button>
                  )}
                  {document.status === 'draft' && currentUser?.permissions?.includes('review') && (
                    <>
                      {canStartReview() ? (
                        <Button
                          variant="contained"
                          startIcon={<Send />}
                          onClick={handleStartReview}
                          fullWidth
                        >
                          Start Review
                        </Button>
                      ) : (
                        <Button
                          variant="outlined"
                          disabled
                          fullWidth
                          title="Please upload a document file before starting review"
                        >
                          Upload File First
                        </Button>
                      )}
                    </>
                  )}
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Workflow Tab */}
        <TabPanel value={tabValue} index={1}>
          <DocumentWorkflowPanel
            document={document}
            currentUser={currentUser}
            onWorkflowUpdate={() => {
              // Refresh document data and close modal
              onClose()
              window.location.reload() // Simple refresh for now
            }}
          />
        </TabPanel>

        {/* Versions Tab */}
        <TabPanel value={tabValue} index={2}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Document Versions
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Version history will be implemented in Phase 2
            </Typography>
          </Paper>
        </TabPanel>

        {/* Dependencies Tab */}
        <TabPanel value={tabValue} index={3}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Document Dependencies
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Document dependencies management will be implemented in Phase 2
            </Typography>
          </Paper>
        </TabPanel>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>

      {/* File Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Upload File for {document.title}
        </DialogTitle>
        <DialogContent>
          <DocumentUpload
            documentId={document.id}
            onUploadComplete={(result) => {
              console.log('Upload completed:', result)
              setUploadDialogOpen(false)
              // Don't close the detail modal, just refresh the document data
              if (onDocumentUpdate) {
                onDocumentUpdate() // Refresh the documents list
              }
              // Remove the page reload that was causing logout
            }}
            onError={(error) => {
              console.error('Upload error:', error)
              alert('Upload failed: ' + error.message)
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  )
}

export default DocumentDetailModal