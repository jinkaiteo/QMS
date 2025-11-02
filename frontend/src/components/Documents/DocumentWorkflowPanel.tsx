import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material'
import {
  Assignment,
  CheckCircle,
  Cancel,
  Send,
  Person,
  Schedule
} from '@mui/icons-material'
import { documentsService, Document } from '../../services/documentsService'

interface WorkflowStep {
  label: string
  description: string
  status: 'completed' | 'active' | 'pending'
  assignedTo?: string
  completedAt?: string
  comments?: string
}

interface DocumentWorkflowPanelProps {
  document: Document
  currentUser: any
  onWorkflowUpdate?: () => void
}

const DocumentWorkflowPanel: React.FC<DocumentWorkflowPanelProps> = ({
  document,
  currentUser,
  onWorkflowUpdate
}) => {
  const [activeStep, setActiveStep] = useState(0)
  const [workflows, setWorkflows] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [actionType, setActionType] = useState<'review' | 'approval' | null>(null)
  const [comments, setComments] = useState('')
  const [effectiveDate, setEffectiveDate] = useState('')
  const [selectedReviewer, setSelectedReviewer] = useState<number>(1)
  const [selectedApprover, setSelectedApprover] = useState<number>(1)

  // Mock users for demonstration
  const mockUsers = [
    { id: 1, name: 'John Smith (QA Manager)', role: 'qa_manager' },
    { id: 2, name: 'Sarah Johnson (Technical Writer)', role: 'technical_writer' },
    { id: 3, name: 'Mike Wilson (Department Head)', role: 'department_head' },
    { id: 4, name: 'Lisa Brown (Quality Director)', role: 'quality_director' }
  ]

  const getWorkflowSteps = (): WorkflowStep[] => {
    const status = document.status.toLowerCase()
    
    return [
      {
        label: 'Document Created',
        description: `Document created by ${document.author.full_name}`,
        status: 'completed'
      },
      {
        label: 'Technical Review',
        description: 'Technical content and accuracy review',
        status: ['pending_review', 'under_review', 'pending_approval', 'approved'].includes(status) ? 'completed' : 
               status === 'draft' ? 'pending' : 'pending'
      },
      {
        label: 'Final Approval', 
        description: 'Management approval and authorization',
        status: status === 'approved' ? 'completed' : 
               status === 'pending_approval' ? 'active' : 'pending'
      },
      {
        label: 'Effective',
        description: 'Document is active and in use',
        status: status === 'approved' ? 'completed' : 'pending'
      }
    ]
  }

  const canStartReview = () => {
    return document.status === 'draft' && currentUser?.permissions?.includes('review')
  }

  const canSubmitReview = () => {
    return document.status === 'pending_review' && currentUser?.permissions?.includes('review')
  }

  const canSubmitApproval = () => {
    return document.status === 'pending_approval' && currentUser?.permissions?.includes('approve')
  }

  const handleStartWorkflow = async (type: 'review' | 'approval') => {
    try {
      setLoading(true)
      setError(null)

      if (type === 'review') {
        await documentsService.startReviewWorkflow(document.id, selectedReviewer)
        await documentsService.updateDocumentStatus(document.id, 'pending_review', 'Review workflow initiated')
      } else {
        await documentsService.startApprovalWorkflow(document.id, selectedApprover)
        await documentsService.updateDocumentStatus(document.id, 'pending_approval', 'Approval workflow initiated')
      }

      onWorkflowUpdate?.()
      setActionType(null)
    } catch (error) {
      console.error('Error starting workflow:', error)
      setError(documentsService.handleError(error))
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitAction = async (approved: boolean) => {
    try {
      setLoading(true)
      setError(null)

      if (!comments.trim()) {
        setError('Please provide comments')
        return
      }

      const mockWorkflowId = 1 // In real implementation, get from current workflow

      if (actionType === 'review') {
        await documentsService.submitReview(mockWorkflowId, approved, comments)
        const newStatus = approved ? 'pending_approval' : 'draft'
        const reason = approved ? 'Review approved, pending final approval' : 'Review rejected, returned to draft'
        await documentsService.updateDocumentStatus(document.id, newStatus, reason)
      } else if (actionType === 'approval') {
        if (approved && !effectiveDate) {
          setError('Please provide an effective date for approval')
          return
        }
        await documentsService.submitApproval(mockWorkflowId, approved, comments, effectiveDate)
        const newStatus = approved ? 'approved' : 'draft'
        const reason = approved ? 'Document approved and effective' : 'Document rejected, returned to draft'
        await documentsService.updateDocumentStatus(document.id, newStatus, reason)
      }

      setComments('')
      setEffectiveDate('')
      setActionType(null)
      onWorkflowUpdate?.()
    } catch (error) {
      console.error('Error submitting action:', error)
      setError(documentsService.handleError(error))
    } finally {
      setLoading(false)
    }
  }

  const workflowSteps = getWorkflowSteps()
  const currentStepIndex = workflowSteps.findIndex(step => step.status === 'active')

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Workflow Status
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Current Status */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Chip
            label={document.status.replace(/_/g, ' ').toUpperCase()}
            color={
              document.status === 'approved' ? 'success' :
              document.status === 'pending_review' ? 'info' :
              document.status === 'pending_approval' ? 'warning' : 'default'
            }
            size="medium"
          />
          {loading && <CircularProgress size={20} />}
        </Box>

        {/* Workflow Stepper */}
        <Stepper activeStep={currentStepIndex >= 0 ? currentStepIndex : workflowSteps.length} orientation="vertical">
          {workflowSteps.map((step, index) => (
            <Step key={step.label} completed={step.status === 'completed'}>
              <StepLabel
                icon={
                  step.status === 'completed' ? <CheckCircle color="success" /> :
                  step.status === 'active' ? <Schedule color="primary" /> :
                  <Assignment color="disabled" />
                }
              >
                <Typography variant="subtitle2">{step.label}</Typography>
              </StepLabel>
              <StepContent>
                <Typography variant="body2" color="text.secondary">
                  {step.description}
                </Typography>
                {step.assignedTo && (
                  <Typography variant="caption" color="text.secondary">
                    Assigned to: {step.assignedTo}
                  </Typography>
                )}
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Action Buttons */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Available Actions
        </Typography>

        {/* Start Review */}
        {canStartReview() && !actionType && (
          <Box sx={{ mb: 2 }}>
            <Button
              variant="contained"
              startIcon={<Send />}
              onClick={() => setActionType('review')}
              fullWidth
            >
              Start Review Process
            </Button>
          </Box>
        )}

        {/* Submit Review */}
        {canSubmitReview() && !actionType && (
          <Box sx={{ mb: 2 }}>
            <Button
              variant="contained"
              color="info"
              startIcon={<CheckCircle />}
              onClick={() => setActionType('review')}
              fullWidth
            >
              Submit Review
            </Button>
          </Box>
        )}

        {/* Submit Approval */}
        {canSubmitApproval() && !actionType && (
          <Box sx={{ mb: 2 }}>
            <Button
              variant="contained"
              color="success"
              startIcon={<CheckCircle />}
              onClick={() => setActionType('approval')}
              fullWidth
            >
              Submit Approval
            </Button>
          </Box>
        )}

        {/* Action Forms */}
        {actionType === 'review' && canStartReview() && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Start Review Workflow
            </Typography>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Select Reviewer</InputLabel>
              <Select
                value={selectedReviewer}
                onChange={(e) => setSelectedReviewer(e.target.value as number)}
              >
                {mockUsers.filter(u => u.role.includes('reviewer') || u.role.includes('qa')).map(user => (
                  <MenuItem key={user.id} value={user.id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Person fontSize="small" />
                      {user.name}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                onClick={() => handleStartWorkflow('review')}
                disabled={loading}
              >
                Start Review
              </Button>
              <Button variant="outlined" onClick={() => setActionType(null)}>
                Cancel
              </Button>
            </Box>
          </Box>
        )}

        {actionType === 'review' && canSubmitReview() && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Submit Review Decision
            </Typography>
            <TextField
              label="Review Comments"
              multiline
              rows={3}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              fullWidth
              sx={{ mb: 2 }}
              required
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                color="success"
                onClick={() => handleSubmitAction(true)}
                disabled={loading}
              >
                Approve Review
              </Button>
              <Button
                variant="outlined"
                color="error"
                onClick={() => handleSubmitAction(false)}
                disabled={loading}
              >
                Reject Review
              </Button>
              <Button variant="outlined" onClick={() => setActionType(null)}>
                Cancel
              </Button>
            </Box>
          </Box>
        )}

        {actionType === 'approval' && canSubmitApproval() && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Submit Final Approval
            </Typography>
            <TextField
              label="Approval Comments"
              multiline
              rows={3}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              fullWidth
              sx={{ mb: 2 }}
              required
            />
            <TextField
              label="Effective Date"
              type="date"
              value={effectiveDate}
              onChange={(e) => setEffectiveDate(e.target.value)}
              fullWidth
              sx={{ mb: 2 }}
              InputLabelProps={{ shrink: true }}
              required
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                color="success"
                onClick={() => handleSubmitAction(true)}
                disabled={loading}
              >
                Approve Document
              </Button>
              <Button
                variant="outlined"
                color="error"
                onClick={() => handleSubmitAction(false)}
                disabled={loading}
              >
                Reject Document
              </Button>
              <Button variant="outlined" onClick={() => setActionType(null)}>
                Cancel
              </Button>
            </Box>
          </Box>
        )}

        {!actionType && !canStartReview() && !canSubmitReview() && !canSubmitApproval() && (
          <Typography variant="body2" color="text.secondary">
            No workflow actions available for your current permissions and the document status.
          </Typography>
        )}
      </Paper>
    </Box>
  )
}

export default DocumentWorkflowPanel