import React, { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
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
  Chip,
  Switch,
  FormControlLabel,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  LinearProgress
} from '@mui/material'
import { 
  Save, 
  Cancel, 
  Upload, 
  CloudUpload as UploadIcon,
  InsertDriveFile as FileIcon,
  Delete as DeleteIcon,
  CheckCircle as SuccessIcon
} from '@mui/icons-material'
import { documentsService, DocumentType, DocumentCategory, CreateDocumentRequest } from '../../services/documentsService'
import { apiClient } from '../../services/apiClient'

interface UploadFile {
  file: File
  id: string
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

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
  
  // File upload state
  const [includeFiles, setIncludeFiles] = useState(false)
  const [files, setFiles] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)

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

  // File upload functionality
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadFile[] = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      progress: 0,
      status: 'pending'
    }))
    setFiles(prev => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: false, // Only one file per document
    disabled: !includeFiles || files.length > 0 // Disable if already have a file
  })

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleSubmit = async () => {
    try {
      setLoading(true)
      setUploading(true)
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

      if (includeFiles && files.length === 0) {
        setError('Please add a file or turn off "Include files with this document"')
        return
      }

      if (includeFiles && files.length > 0) {
        // Create document with files using upload endpoint
        await createDocumentWithFiles()
      } else {
        // Create metadata-only document
        await documentsService.createDocument(formData)
      }
      
      // Reset form
      resetForm()
      onDocumentCreated?.()
      onClose()
    } catch (error) {
      console.error('Error creating document:', error)
      setError(documentsService.handleError(error))
    } finally {
      setLoading(false)
      setUploading(false)
    }
  }

  const createDocumentWithFiles = async () => {
    for (const uploadFile of files) {
      if (uploadFile.status === 'pending') {
        const uploadFormData = new FormData()
        uploadFormData.append('file', uploadFile.file)
        uploadFormData.append('title', formData.title)
        uploadFormData.append('description', formData.description || '')
        uploadFormData.append('document_type_id', formData.document_type_id.toString())
        if (formData.category_id) {
          uploadFormData.append('category_id', formData.category_id.toString())
        }
        uploadFormData.append('confidentiality_level', formData.confidentiality_level)
        uploadFormData.append('is_controlled', formData.is_controlled.toString())
        if (formData.tags && formData.tags.length > 0) {
          uploadFormData.append('tags', JSON.stringify(formData.tags))
        }

        // Update progress
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { ...f, status: 'uploading', progress: 50 }
            : f
        ))

        try {
          const response = await apiClient.post('/api/v1/documents/upload', uploadFormData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          })

          setFiles(prev => prev.map(f => 
            f.id === uploadFile.id 
              ? { ...f, status: 'success', progress: 100 }
              : f
          ))
        } catch (error) {
          setFiles(prev => prev.map(f => 
            f.id === uploadFile.id 
              ? { ...f, status: 'error', progress: 0, error: 'Upload failed' }
              : f
          ))
          throw error
        }
      }
    }
  }

  const resetForm = () => {
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
    setFiles([])
    setIncludeFiles(false)
    setTagInput('')
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

          {/* File Upload Section */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              File Upload (Optional)
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={includeFiles}
                  onChange={(e) => {
                    setIncludeFiles(e.target.checked)
                    if (!e.target.checked) {
                      setFiles([])
                    }
                  }}
                />
              }
              label="Include files with this document"
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {includeFiles 
                ? "Add files now to create the document ready for review"
                : "Document will be created without files. You can add files later."
              }
            </Typography>
          </Grid>

          {/* File Upload Area */}
          {includeFiles && (
            <>
              <Grid item xs={12}>
                <Card sx={{ mt: 2 }}>
                  <CardContent>
                    {/* Drag and Drop Area */}
                    <Box
                      {...getRootProps()}
                      sx={{
                        border: '2px dashed',
                        borderColor: isDragActive ? 'primary.main' : 'grey.300',
                        borderRadius: 2,
                        p: 3,
                        textAlign: 'center',
                        cursor: 'pointer',
                        bgcolor: isDragActive ? 'action.hover' : 'background.paper',
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          borderColor: 'primary.main',
                          bgcolor: 'action.hover',
                        },
                      }}
                    >
                      <input {...getInputProps()} />
                      <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="h6" gutterBottom>
                        {files.length > 0 ? 'One file already selected' :
                         isDragActive ? 'Drop file here...' : 'Drag & drop file here'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {files.length > 0 ? 'Remove the current file to select a different one' :
                         'or click to select a file'}
                      </Typography>
                      <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                        Supported: PDF, Word, Excel, Images (Max 50MB each)
                      </Typography>
                    </Box>

                    {/* File List */}
                    {files.length > 0 && (
                      <Box sx={{ mt: 3 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Selected File
                        </Typography>
                        <List dense>
                          {files.map((uploadFile) => (
                            <ListItem key={uploadFile.id} divider>
                              <ListItemIcon>
                                {uploadFile.status === 'success' ? (
                                  <SuccessIcon color="success" />
                                ) : uploadFile.status === 'error' ? (
                                  <FileIcon color="error" />
                                ) : (
                                  <FileIcon />
                                )}
                              </ListItemIcon>
                              <ListItemText
                                primary={uploadFile.file.name}
                                secondary={`${formatFileSize(uploadFile.file.size)}${uploadFile.status === 'error' ? ' - Upload failed' : ''}`}
                              />
                              {uploadFile.status === 'uploading' && (
                                <Box sx={{ width: 100, mr: 2 }}>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={uploadFile.progress}
                                  />
                                </Box>
                              )}
                              <IconButton
                                edge="end"
                                onClick={() => removeFile(uploadFile.id)}
                                disabled={uploadFile.status === 'uploading'}
                                size="small"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </>
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
          disabled={loading || uploading}
          startIcon={loading || uploading ? <CircularProgress size={20} /> : <Save />}
        >
          {uploading ? 'Uploading...' : loading ? 'Creating...' : 
           includeFiles ? 'Create Document with Files' : 'Create Document'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default CreateDocumentModal