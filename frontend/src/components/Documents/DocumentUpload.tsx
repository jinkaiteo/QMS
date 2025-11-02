import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  Alert,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  InsertDriveFile as FileIcon,
  Delete as DeleteIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material'
import { apiClient } from '../../services/apiClient'

interface DocumentType {
  id: number
  name: string
  code: string
}

interface DocumentCategory {
  id: number
  name: string
  code: string
}

interface UploadFile {
  file: File
  id: string
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
  documentId?: number
}

interface DocumentUploadProps {
  documentId?: number // If provided, attach to existing document
  onUploadComplete?: (result: any) => void
  onError?: (error: any) => void
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ 
  documentId, 
  onUploadComplete,
  onError 
}) => {
  // This component is now only used for adding files to existing documents
  // All new document creation with files should use the enhanced CreateDocumentModal
  const [files, setFiles] = useState<UploadFile[]>([])
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([])
  const [categories, setCategories] = useState<DocumentCategory[]>([])
  const [selectedType, setSelectedType] = useState<number | ''>('')
  const [selectedCategory, setSelectedCategory] = useState<number | ''>('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [uploadReason, setUploadReason] = useState('')
  const [versionNotes, setVersionNotes] = useState('')
  const [uploading, setUploading] = useState(false)
  
  const isExistingDocument = Boolean(documentId)

  // Load document types and categories only for new documents
  React.useEffect(() => {
    if (!isExistingDocument) {
      loadDocumentTypes()
      loadCategories()
    }
  }, [isExistingDocument])

  const loadDocumentTypes = async () => {
    try {
      const response = await apiClient.get<DocumentType[]>('/api/v1/documents/types')
      setDocumentTypes(response.data)
    } catch (error) {
      console.error('Failed to load document types:', error)
    }
  }

  const loadCategories = async () => {
    try {
      const response = await apiClient.get<DocumentCategory[]>('/api/v1/documents/categories')
      setCategories(response.data)
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  }

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Only take the first file since we only allow one file per document
    if (acceptedFiles.length > 0) {
      const newFile: UploadFile = {
        file: acceptedFiles[0],
        id: Math.random().toString(36).substr(2, 9),
        progress: 0,
        status: 'pending'
      }
      setFiles([newFile]) // Replace any existing file
    }
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
    disabled: uploading || files.length > 0 // Disable if uploading or already have a file
  })

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const uploadFile = async (uploadFile: UploadFile) => {
    // Validation based on mode
    if (isExistingDocument) {
      if (!uploadReason) {
        return
      }
    } else {
      if (!selectedType || !title) {
        return
      }
    }

    const formData = new FormData()
    formData.append('file', uploadFile.file)

    if (isExistingDocument) {
      // For existing documents, only upload reason and version notes
      formData.append('upload_reason', uploadReason)
      if (versionNotes) {
        formData.append('version_notes', versionNotes)
      }
    } else {
      // For new documents, include metadata
      formData.append('title', title)
      formData.append('description', description)
      formData.append('document_type_id', selectedType.toString())
      if (selectedCategory) {
        formData.append('category_id', selectedCategory.toString())
      }
    }

    try {
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'uploading', progress: 50 }
          : f
      ))

      // Use different endpoints based on mode
      const endpoint = isExistingDocument 
        ? `/api/v1/documents/files/${documentId}/upload`
        : '/api/v1/documents/upload'

      const response = await apiClient.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { 
              ...f, 
              status: 'success', 
              progress: 100,
              documentId: isExistingDocument ? documentId : response.data.document_id 
            }
          : f
      ))

      // Call success callback
      if (onUploadComplete) {
        onUploadComplete(response.data)
      }

    } catch (error: any) {
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { 
              ...f, 
              status: 'error', 
              progress: 0,
              error: error.response?.data?.detail || 'Upload failed'
            }
          : f
      ))

      // Call error callback
      if (onError) {
        onError(error)
      }
    }
  }

  const uploadAllFiles = async () => {
    if (isExistingDocument) {
      if (!uploadReason) {
        alert('Please provide an upload reason')
        return
      }
    } else {
      if (!selectedType || !title) {
        alert('Please fill in required fields: Title and Document Type')
        return
      }
    }

    setUploading(true)
    
    const pendingFiles = files.filter(f => f.status === 'pending')
    
    for (const file of pendingFiles) {
      await uploadFile(file)
    }
    
    setUploading(false)
  }

  const clearCompleted = () => {
    setFiles(prev => prev.filter(f => f.status !== 'success'))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        {isExistingDocument ? 'Upload File to Document' : 'Document Upload (Deprecated - Use Create Document instead)'}
      </Typography>

      {/* Upload Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ mb: 3 }}>
            {/* Show document metadata fields only for new documents */}
            {!isExistingDocument && (
              <>
                <TextField
                  fullWidth
                  label="Document Title *"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  margin="normal"
                  required
                />
                
                <TextField
                  fullWidth
                  label="Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  margin="normal"
                  multiline
                  rows={3}
                />

                <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                  <FormControl fullWidth required>
                    <InputLabel>Document Type</InputLabel>
                    <Select
                      value={selectedType}
                      onChange={(e) => setSelectedType(e.target.value as number)}
                      label="Document Type"
                    >
                      {documentTypes.map((type) => (
                        <MenuItem key={type.id} value={type.id}>
                          {type.name} ({type.code})
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value as number)}
                      label="Category"
                    >
                      <MenuItem value="">
                        <em>None</em>
                      </MenuItem>
                      {categories.map((category) => (
                        <MenuItem key={category.id} value={category.id}>
                          {category.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
              </>
            )}

            {/* Show upload reason and version notes for existing documents */}
            {isExistingDocument && (
              <>
                <TextField
                  fullWidth
                  label="Upload Reason *"
                  value={uploadReason}
                  onChange={(e) => setUploadReason(e.target.value)}
                  margin="normal"
                  required
                  placeholder="e.g., Initial version, Updated content, Corrections"
                />
                
                <TextField
                  fullWidth
                  label="Version Notes"
                  value={versionNotes}
                  onChange={(e) => setVersionNotes(e.target.value)}
                  margin="normal"
                  multiline
                  rows={2}
                  placeholder="Optional notes about this version"
                />
              </>
            )}
          </Box>

          {/* Drag and Drop Area */}
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderRadius: 2,
              p: 4,
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
              {files.length > 0 ? 'One file selected' :
               isDragActive ? 'Drop file here...' : 'Drag & drop file here'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {files.length > 0 ? 'Remove the current file to select a different one' :
               'or click to select a file'}
            </Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Supported: PDF, Word, Excel, PowerPoint, Images (Max 50MB each)
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Selected File
              </Typography>
              <Box>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={clearCompleted}
                  sx={{ mr: 1 }}
                  disabled={!files.some(f => f.status === 'success')}
                >
                  Clear Completed
                </Button>
                <Button
                  variant="contained"
                  onClick={uploadAllFiles}
                  disabled={
                    uploading || 
                    files.every(f => f.status !== 'pending') || 
                    (isExistingDocument ? !uploadReason : (!selectedType || !title))
                  }
                  startIcon={<UploadIcon />}
                >
                  {uploading ? 'Uploading...' : (isExistingDocument ? 'Upload to Document' : 'Upload File')}
                </Button>
              </Box>
            </Box>

            <List>
              {files.map((uploadFile) => (
                <ListItem key={uploadFile.id} divider>
                  <ListItemIcon>
                    {uploadFile.status === 'success' ? (
                      <SuccessIcon color="success" />
                    ) : (
                      <FileIcon />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={uploadFile.file.name}
                    secondary={`${formatFileSize(uploadFile.file.size)}${uploadFile.status === 'error' ? ' - Upload failed' : ''}${uploadFile.status === 'success' ? ` - Document ID: ${uploadFile.documentId}` : ''}`}
                  />
                  {uploadFile.status === 'uploading' && (
                    <Box sx={{ width: 100, mr: 2 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={uploadFile.progress}
                      />
                    </Box>
                  )}
                  {uploadFile.status === 'success' && (
                    <Chip 
                      label="Success" 
                      color="success" 
                      size="small" 
                      sx={{ mr: 1 }}
                    />
                  )}
                  <IconButton
                    edge="end"
                    onClick={() => removeFile(uploadFile.id)}
                    disabled={uploadFile.status === 'uploading'}
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default DocumentUpload