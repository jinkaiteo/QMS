import React, { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Box,
  Typography,
  Grid,
  Alert,
  CircularProgress,
  Chip
} from '@mui/material'
import { Save, Cancel, Upload } from '@mui/icons-material'
import { documentsService, DocumentType, DocumentCategory, CreateDocumentRequest } from '../../services/documentsService'

interface CreateDocumentModalProps {
  open: boolean
  onClose: () => void
  onDocumentCreated?: () => void
}

const CreateDocumentModal: React.FC<CreateDocumentModalProps> = ({
  open,
  onClose,
  onDocumentCreated
}) => {
  const [formData, setFormData] = useState<CreateDocumentRequest>({
    title: '',
    description: '',
    document_number: '',
    document_type_id: 0,
    category_id: undefined,
    confidentiality_level: 'internal',
    is_controlled: true,
    tags: []
  })
  
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([])
  const [documentCategories, setDocumentCategories] = useState<DocumentCategory[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tagInput, setTagInput] = useState('')

  useEffect(() => {
    if (open) {
      loadDocumentTypes()
      loadDocumentCategories()
      // Generate initial document number
      generateDocumentNumber()
    }
  }, [open])

  const loadDocumentTypes = async () => {
    try {
      const types = await documentsService.getDocumentTypes()
      setDocumentTypes(types)
    } catch (error) {
      console.error('Error loading document types:', error)
    }
  }

  const loadDocumentCategories = async () => {
    try {
      const categories = await documentsService.getDocumentCategories()
      setDocumentCategories(categories)
    } catch (error) {
      console.error('Error loading document categories:', error)
    }
  }

  const generateDocumentNumber = () => {
    // Simple document number generation - in real app, this would be handled by backend
    const timestamp = Date.now().toString().slice(-6)
    setFormData(prev => ({
      ...prev,
      document_number: `DOC-${timestamp}`
    }))
  }

  const handleInputChange = (field: keyof CreateDocumentRequest) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | any
  ) => {
    const value = event.target.value
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))

    // Auto-generate document number based on type
    if (field === 'document_type_id' && value) {
      const selectedType = documentTypes.find(type => type.id === value)
      if (selectedType && selectedType.prefix) {
        const timestamp = Date.now().toString().slice(-6)
        setFormData(prev => ({
          ...prev,
          document_number: `${selectedType.prefix}-${timestamp}`
        }))
      }
    }
  }

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...(prev.tags || []), tagInput.trim()]
      }))
      setTagInput('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: (prev.tags || []).filter(tag => tag !== tagToRemove)
    }))
  }

  const handleSubmit = async () => {
    try {
      setLoading(true)
      setError(null)

      // Validate required fields
      if (!formData.title.trim()) {
        setError('Document title is required')
        return
      }
      if (!formData.document_number.trim()) {
        setError('Document number is required')
        return
      }
      if (!formData.document_type_id) {
        setError('Document type is required')
        return
      }

      // Create the document
      await documentsService.createDocument(formData)
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        document_number: '',
        document_type_id: 0,
        category_id: undefined,
        confidentiality_level: 'internal',
        is_controlled: true,
        tags: []
      })

      onDocumentCreated?.()
      onClose()
    } catch (error) {
      console.error('Error creating document:', error)
      setError(documentsService.handleError(error))
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    if (!loading) {
      onClose()
    }
  }

  const selectedType = documentTypes.find(type => type.id === formData.document_type_id)

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Create New Document
      </DialogTitle>
      <Box sx={{ px: 3, pb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Create a new document in the QMS system
        </Typography>
      </Box>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3} sx={{ mt: 1 }}>
          {/* Basic Information */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>
          </Grid>

          <Grid item xs={12} md={8}>
            <TextField
              label="Document Title"
              value={formData.title}
              onChange={handleInputChange('title')}
              fullWidth
              required
              placeholder="Enter descriptive document title"
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Document Number"
              value={formData.document_number}
              onChange={handleInputChange('document_number')}
              fullWidth
              required
              placeholder="Auto-generated"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="Description"
              value={formData.description}
              onChange={handleInputChange('description')}
              fullWidth
              multiline
              rows={3}
              placeholder="Provide a detailed description of the document purpose and content"
            />
          </Grid>

          {/* Classification */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Classification
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth required>
              <InputLabel>Document Type</InputLabel>
              <Select
                value={formData.document_type_id}
                onChange={handleInputChange('document_type_id')}
                label="Document Type"
              >
                {documentTypes.map(type => (
                  <MenuItem key={type.id} value={type.id}>
                    <Box>
                      <Typography variant="body2">{type.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {type.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={formData.category_id || ''}
                onChange={handleInputChange('category_id')}
                label="Category"
              >
                <MenuItem value="">
                  <em>No category</em>
                </MenuItem>
                {documentCategories.map(category => (
                  <MenuItem key={category.id} value={category.id}>
                    <Box>
                      <Typography variant="body2">{category.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {category.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Confidentiality Level</InputLabel>
              <Select
                value={formData.confidentiality_level}
                onChange={handleInputChange('confidentiality_level')}
                label="Confidentiality Level"
              >
                <MenuItem value="public">Public</MenuItem>
                <MenuItem value="internal">Internal</MenuItem>
                <MenuItem value="confidential">Confidential</MenuItem>
                <MenuItem value="restricted">Restricted</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Document Control</InputLabel>
              <Select
                value={formData.is_controlled ? 'controlled' : 'uncontrolled'}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  is_controlled: e.target.value === 'controlled'
                }))}
                label="Document Control"
              >
                <MenuItem value="controlled">Controlled Document</MenuItem>
                <MenuItem value="uncontrolled">Uncontrolled Document</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Tags */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Tags
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
              {formData.tags?.map((tag, index) => (
                <Chip
                  key={index}
                  label={tag}
                  onDelete={() => handleRemoveTag(tag)}
                  size="small"
                />
              ))}
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                label="Add Tag"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                size="small"
                onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
              />
              <Button
                variant="outlined"
                onClick={handleAddTag}
                disabled={!tagInput.trim()}
              >
                Add
              </Button>
            </Box>
          </Grid>

          {/* Document Type Info */}
          {selectedType && (
            <Grid item xs={12}>
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>{selectedType.name}</strong>: {selectedType.description}
                </Typography>
                {selectedType.is_controlled && (
                  <Typography variant="caption" display="block">
                    This document type requires review and approval workflow.
                  </Typography>
                )}
              </Alert>
            </Grid>
          )}
        </Grid>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button
          variant="outlined"
          onClick={handleClose}
          disabled={loading}
          startIcon={<Cancel />}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : <Save />}
        >
          {loading ? 'Creating...' : 'Create Document'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default CreateDocumentModal