import React, { useState, useRef } from 'react'
import {
  Box,
  Button,
  Typography,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Paper,
} from '@mui/material'
import {
  CloudUpload,
  Delete,
  Description,
  CheckCircle,
  Error,
} from '@mui/icons-material'

interface FileUploadProps {
  acceptedTypes?: string[]
  maxFileSize?: number // in MB
  multiple?: boolean
  onFileSelect?: (files: File[]) => void
  onUploadProgress?: (progress: number) => void
  onUploadComplete?: (results: any[]) => void
  onUploadError?: (error: string) => void
  disabled?: boolean
}

interface UploadFile {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  error?: string
  result?: any
}

const FileUpload: React.FC<FileUploadProps> = ({
  acceptedTypes = ['.pdf', '.docx', '.doc', '.xlsx', '.xls'],
  maxFileSize = 10, // 10MB default
  multiple = false,
  onFileSelect,
  onUploadProgress,
  onUploadComplete,
  onUploadError,
  disabled = false,
}) => {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxFileSize * 1024 * 1024) {
      return `File size exceeds ${maxFileSize}MB limit`
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    if (acceptedTypes.length > 0 && !acceptedTypes.includes(fileExtension)) {
      return `File type ${fileExtension} is not supported. Accepted types: ${acceptedTypes.join(', ')}`
    }

    return null
  }

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return

    const selectedFiles = Array.from(files)
    const validFiles: File[] = []
    const errors: string[] = []

    selectedFiles.forEach(file => {
      const validationError = validateFile(file)
      if (validationError) {
        errors.push(`${file.name}: ${validationError}`)
      } else {
        validFiles.push(file)
      }
    })

    if (errors.length > 0) {
      onUploadError?.(errors.join('\n'))
      return
    }

    const newUploadFiles: UploadFile[] = validFiles.map(file => ({
      file,
      progress: 0,
      status: 'pending',
    }))

    if (multiple) {
      setUploadFiles(prev => [...prev, ...newUploadFiles])
    } else {
      setUploadFiles(newUploadFiles)
    }

    onFileSelect?.(validFiles)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    handleFileSelect(e.dataTransfer.files)
  }

  const removeFile = (index: number) => {
    setUploadFiles(prev => prev.filter((_, i) => i !== index))
  }

  const clearAllFiles = () => {
    setUploadFiles([])
  }

  const updateFileProgress = (index: number, progress: number) => {
    setUploadFiles(prev => prev.map((file, i) => 
      i === index ? { ...file, progress, status: 'uploading' as const } : file
    ))
  }

  const updateFileStatus = (index: number, status: 'completed' | 'error', result?: any, error?: string) => {
    setUploadFiles(prev => prev.map((file, i) => 
      i === index ? { ...file, status, result, error, progress: status === 'completed' ? 100 : file.progress } : file
    ))
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />
      case 'error':
        return <Error color="error" />
      case 'uploading':
        return <CloudUpload color="primary" />
      default:
        return <Description />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'error':
        return 'error'
      case 'uploading':
        return 'primary'
      default:
        return 'default'
    }
  }

  return (
    <Box>
      {/* Upload Area */}
      <Paper
        sx={{
          p: 3,
          border: isDragOver ? 2 : 1,
          borderColor: isDragOver ? 'primary.main' : 'grey.300',
          borderStyle: 'dashed',
          backgroundColor: isDragOver ? 'primary.light' : 'background.paper',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.6 : 1,
          transition: 'all 0.3s ease',
          '&:hover': {
            backgroundColor: disabled ? 'background.paper' : 'grey.50',
          },
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragOver ? 'Drop files here' : 'Upload Files'}
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Drag and drop files here, or click to select files
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Accepted formats: {acceptedTypes.join(', ')} | Max size: {maxFileSize}MB
            {multiple && ' | Multiple files allowed'}
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Button variant="outlined" disabled={disabled}>
              Browse Files
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        hidden
        multiple={multiple}
        accept={acceptedTypes.join(',')}
        onChange={(e) => handleFileSelect(e.target.files)}
        disabled={disabled}
      />

      {/* File List */}
      {uploadFiles.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle1">
              Selected Files ({uploadFiles.length})
            </Typography>
            <Button size="small" onClick={clearAllFiles} disabled={disabled}>
              Clear All
            </Button>
          </Box>

          <List>
            {uploadFiles.map((uploadFile, index) => (
              <ListItem key={index} divider>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getStatusIcon(uploadFile.status)}
                      <Typography variant="subtitle2">
                        {uploadFile.file.name}
                      </Typography>
                      <Chip
                        label={uploadFile.status.toUpperCase()}
                        size="small"
                        color={getStatusColor(uploadFile.status) as any}
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="caption" color="textSecondary">
                        {formatFileSize(uploadFile.file.size)}
                      </Typography>
                      {uploadFile.status === 'uploading' && (
                        <Box sx={{ mt: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={uploadFile.progress} 
                            sx={{ height: 6, borderRadius: 3 }}
                          />
                          <Typography variant="caption" color="textSecondary">
                            {uploadFile.progress}% uploaded
                          </Typography>
                        </Box>
                      )}
                      {uploadFile.error && (
                        <Alert severity="error" sx={{ mt: 1 }}>
                          {uploadFile.error}
                        </Alert>
                      )}
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <IconButton 
                    edge="end" 
                    onClick={() => removeFile(index)}
                    disabled={disabled || uploadFile.status === 'uploading'}
                  >
                    <Delete />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Box>
      )}
    </Box>
  )
}

export default FileUpload