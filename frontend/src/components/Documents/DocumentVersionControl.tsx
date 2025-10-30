import React, { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Tabs,
  Tab,
} from '@mui/material'
import {
  History as VersionIcon,
  Compare as CompareIcon,
  Archive as ArchiveIcon,
  GetApp as DownloadIcon,
  Visibility as ViewIcon,
  AccountTree as GenealogyIcon,
} from '@mui/icons-material'
import { apiClient } from '../../services/apiClient-simple'

interface DocumentVersion {
  id: number
  version_number: string
  file_name: string
  file_size: number
  change_summary: string
  created_by: string
  created_at: string
  approved_by?: string
  approved_at?: string
  is_current: boolean
  file_hash: string
}

interface DocumentVersionControlProps {
  documentId: number
  documentTitle: string
}

const DocumentVersionControl: React.FC<DocumentVersionControlProps> = ({
  documentId,
  documentTitle
}) => {
  const [versions, setVersions] = useState<DocumentVersion[]>([])
  const [selectedVersions, setSelectedVersions] = useState<string[]>([])
  const [comparison, setComparison] = useState<any>(null)
  const [genealogy, setGenealogy] = useState<any>(null)
  const [metrics, setMetrics] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState(0)
  
  // Dialog states
  const [newVersionDialog, setNewVersionDialog] = useState(false)
  const [retireDialog, setRetireDialog] = useState(false)
  const [compareDialog, setCompareDialog] = useState(false)
  const [genealogyDialog, setGenealogyDialog] = useState(false)
  
  // Form states
  const [newVersionFile, setNewVersionFile] = useState<File | null>(null)
  const [changeSummary, setChangeSummary] = useState('')
  const [versionType, setVersionType] = useState('minor')
  const [retirementReason, setRetirementReason] = useState('')

  useEffect(() => {
    loadVersionHistory()
    loadGenealogy()
    loadMetrics()
  }, [documentId])

  const loadVersionHistory = async () => {
    try {
      const response = await apiClient.get(`/v1/versions/history/${documentId}`)
      setVersions(response.data.versions)
    } catch (error) {
      console.error('Failed to load version history:', error)
    }
  }

  const loadGenealogy = async () => {
    try {
      const response = await apiClient.get(`/v1/versions/genealogy/${documentId}`)
      setGenealogy(response.data)
    } catch (error) {
      console.error('Failed to load genealogy:', error)
    }
  }

  const loadMetrics = async () => {
    try {
      const response = await apiClient.get('/v1/versions/lifecycle/metrics')
      setMetrics(response.data)
    } catch (error) {
      console.error('Failed to load metrics:', error)
    }
  }

  const handleCreateVersion = async () => {
    if (!newVersionFile || !changeSummary) {
      alert('Please select a file and provide a change summary')
      return
    }

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', newVersionFile)
      formData.append('change_summary', changeSummary)
      formData.append('version_type', versionType)

      await apiClient.post(`/v1/versions/create-version/${documentId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      setNewVersionDialog(false)
      setNewVersionFile(null)
      setChangeSummary('')
      setVersionType('minor')
      await loadVersionHistory()
      
      alert('New version created successfully!')
    } catch (error: any) {
      alert(`Failed to create version: ${error.response?.data?.detail || 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleCompareVersions = async () => {
    if (selectedVersions.length !== 2) {
      alert('Please select exactly 2 versions to compare')
      return
    }

    try {
      const response = await apiClient.get(
        `/v1/versions/compare/${documentId}?version1=${selectedVersions[0]}&version2=${selectedVersions[1]}`
      )
      setComparison(response.data)
      setCompareDialog(true)
    } catch (error: any) {
      alert(`Failed to compare versions: ${error.response?.data?.detail || 'Unknown error'}`)
    }
  }

  const handleRetireDocument = async () => {
    if (!retirementReason) {
      alert('Please provide a retirement reason')
      return
    }

    setLoading(true)
    try {
      await apiClient.post(`/v1/versions/retire/${documentId}`, {
        retirement_reason: retirementReason
      })

      setRetireDialog(false)
      setRetirementReason('')
      alert('Document retired successfully!')
    } catch (error: any) {
      alert(`Failed to retire document: ${error.response?.data?.detail || 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusColor = (version: DocumentVersion) => {
    if (version.is_current) return 'primary'
    if (version.approved_at) return 'success'
    return 'default'
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Document Version Control
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        {documentTitle}
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Version History" />
          <Tab label="Document Genealogy" />
          <Tab label="Lifecycle Metrics" />
        </Tabs>
      </Box>

      {/* Version History Tab */}
      {activeTab === 0 && (
        <Box>
          <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={<VersionIcon />}
              onClick={() => setNewVersionDialog(true)}
            >
              Create New Version
            </Button>
            <Button
              variant="outlined"
              startIcon={<CompareIcon />}
              onClick={handleCompareVersions}
              disabled={selectedVersions.length !== 2}
            >
              Compare Versions ({selectedVersions.length}/2)
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<ArchiveIcon />}
              onClick={() => setRetireDialog(true)}
            >
              Retire Document
            </Button>
            <Button
              variant="outlined"
              startIcon={<GenealogyIcon />}
              onClick={() => setGenealogyDialog(true)}
            >
              View Genealogy
            </Button>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox">Select</TableCell>
                  <TableCell>Version</TableCell>
                  <TableCell>File Name</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Change Summary</TableCell>
                  <TableCell>Created By</TableCell>
                  <TableCell>Created Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {versions.map((version) => (
                  <TableRow key={version.id}>
                    <TableCell padding="checkbox">
                      <input
                        type="checkbox"
                        checked={selectedVersions.includes(version.version_number)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            if (selectedVersions.length < 2) {
                              setSelectedVersions([...selectedVersions, version.version_number])
                            }
                          } else {
                            setSelectedVersions(selectedVersions.filter(v => v !== version.version_number))
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={version.version_number}
                        color={getStatusColor(version) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{version.file_name}</TableCell>
                    <TableCell>{formatFileSize(version.file_size)}</TableCell>
                    <TableCell>{version.change_summary}</TableCell>
                    <TableCell>{version.created_by}</TableCell>
                    <TableCell>
                      {new Date(version.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {version.is_current ? (
                        <Chip label="Current" color="primary" size="small" />
                      ) : version.approved_at ? (
                        <Chip label="Approved" color="success" size="small" />
                      ) : (
                        <Chip label="Draft" color="default" size="small" />
                      )}
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" title="View">
                        <ViewIcon />
                      </IconButton>
                      <IconButton size="small" title="Download">
                        <DownloadIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Document Genealogy Tab */}
      {activeTab === 1 && genealogy && (
        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Document Family Tree
              </Typography>
              
              {genealogy.supersedes.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" color="primary">
                    This document supersedes:
                  </Typography>
                  {genealogy.supersedes.map((doc: any) => (
                    <Chip
                      key={doc.id}
                      label={`${doc.document_number}: ${doc.title}`}
                      variant="outlined"
                      sx={{ m: 0.5 }}
                    />
                  ))}
                </Box>
              )}

              <Box sx={{ mb: 3, p: 2, bgcolor: 'primary.light', borderRadius: 1 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                  Current Document: {genealogy.current_document.document_number}
                </Typography>
                <Typography variant="body2">
                  {genealogy.current_document.title}
                </Typography>
                <Typography variant="body2">
                  Version: {genealogy.current_document.current_version} | 
                  Status: {genealogy.current_document.status}
                </Typography>
              </Box>

              {genealogy.superseded_by.length > 0 && (
                <Box>
                  <Typography variant="subtitle1" color="error">
                    This document is superseded by:
                  </Typography>
                  {genealogy.superseded_by.map((doc: any) => (
                    <Chip
                      key={doc.id}
                      label={`${doc.document_number}: ${doc.title}`}
                      color="error"
                      variant="outlined"
                      sx={{ m: 0.5 }}
                    />
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Lifecycle Metrics Tab */}
      {activeTab === 2 && metrics && (
        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Document Lifecycle Metrics
              </Typography>
              
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 3 }}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.light', borderRadius: 1 }}>
                  <Typography variant="h4" color="primary">
                    {metrics.total_documents}
                  </Typography>
                  <Typography variant="body2">Total Documents</Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                  <Typography variant="h4" color="success.main">
                    {metrics.version_statistics.total_versions}
                  </Typography>
                  <Typography variant="body2">Total Versions</Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="h4" color="info.main">
                    {metrics.version_statistics.average_versions_per_document}
                  </Typography>
                  <Typography variant="body2">Avg Versions/Doc</Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                  <Typography variant="h4" color="warning.main">
                    {metrics.recent_activity.documents_needing_review}
                  </Typography>
                  <Typography variant="body2">Need Review</Typography>
                </Box>
              </Box>

              <Typography variant="subtitle1" gutterBottom>
                Status Distribution
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.entries(metrics.status_distribution).map(([status, count]: [string, any]) => (
                  <Chip
                    key={status}
                    label={`${status}: ${count}`}
                    variant="outlined"
                    size="small"
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* New Version Dialog */}
      <Dialog open={newVersionDialog} onClose={() => setNewVersionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Version</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Version Type</InputLabel>
              <Select
                value={versionType}
                onChange={(e) => setVersionType(e.target.value)}
                label="Version Type"
              >
                <MenuItem value="major">Major (x.0)</MenuItem>
                <MenuItem value="minor">Minor (x.y)</MenuItem>
                <MenuItem value="revision">Revision (x.y.z)</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Change Summary"
              multiline
              rows={3}
              value={changeSummary}
              onChange={(e) => setChangeSummary(e.target.value)}
              margin="normal"
              required
            />

            <Button
              variant="outlined"
              component="label"
              fullWidth
              sx={{ mt: 2 }}
            >
              {newVersionFile ? newVersionFile.name : 'Select File'}
              <input
                type="file"
                hidden
                onChange={(e) => setNewVersionFile(e.target.files?.[0] || null)}
              />
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewVersionDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateVersion} 
            variant="contained"
            disabled={loading || !newVersionFile || !changeSummary}
          >
            {loading ? 'Creating...' : 'Create Version'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Retire Document Dialog */}
      <Dialog open={retireDialog} onClose={() => setRetireDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Retire Document</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This action will mark the document as retired and remove it from active use.
          </Alert>
          <TextField
            fullWidth
            label="Retirement Reason"
            multiline
            rows={3}
            value={retirementReason}
            onChange={(e) => setRetirementReason(e.target.value)}
            margin="normal"
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRetireDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleRetireDocument} 
            color="error"
            variant="contained"
            disabled={loading || !retirementReason}
          >
            {loading ? 'Retiring...' : 'Retire Document'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Version Comparison Dialog */}
      <Dialog open={compareDialog} onClose={() => setCompareDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Version Comparison</DialogTitle>
        <DialogContent>
          {comparison && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Comparing versions {comparison.version1.version_number} and {comparison.version2.version_number}
              </Typography>
              
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mt: 2 }}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" color="primary">
                      Version {comparison.version1.version_number}
                    </Typography>
                    <Typography variant="body2">File: {comparison.version1.file_name}</Typography>
                    <Typography variant="body2">Size: {formatFileSize(comparison.version1.file_size)}</Typography>
                    <Typography variant="body2">Created: {new Date(comparison.version1.created_at).toLocaleString()}</Typography>
                    <Typography variant="body2">By: {comparison.version1.created_by}</Typography>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" color="primary">
                      Version {comparison.version2.version_number}
                    </Typography>
                    <Typography variant="body2">File: {comparison.version2.file_name}</Typography>
                    <Typography variant="body2">Size: {formatFileSize(comparison.version2.file_size)}</Typography>
                    <Typography variant="body2">Created: {new Date(comparison.version2.created_at).toLocaleString()}</Typography>
                    <Typography variant="body2">By: {comparison.version2.created_by}</Typography>
                  </CardContent>
                </Card>
              </Box>

              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1">Differences:</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {comparison.differences.file_name_changed && (
                    <Chip label="File name changed" color="warning" size="small" />
                  )}
                  {comparison.differences.content_changed && (
                    <Chip label="Content changed" color="info" size="small" />
                  )}
                  {comparison.differences.file_size_changed && (
                    <Chip 
                      label={`Size ${comparison.differences.size_difference_bytes > 0 ? 'increased' : 'decreased'} by ${Math.abs(comparison.differences.size_difference_bytes)} bytes`}
                      color="secondary" 
                      size="small" 
                    />
                  )}
                  {!comparison.differences.file_name_changed && !comparison.differences.content_changed && !comparison.differences.file_size_changed && (
                    <Chip label="No differences detected" color="success" size="small" />
                  )}
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompareDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Genealogy Dialog */}
      <Dialog open={genealogyDialog} onClose={() => setGenealogyDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Document Genealogy</DialogTitle>
        <DialogContent>
          {genealogy && (
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Document Family Tree
              </Typography>
              <Box sx={{ textAlign: 'center' }}>
                {genealogy.supersedes.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary">Supersedes</Typography>
                    {genealogy.supersedes.map((doc: any) => (
                      <Card key={doc.id} sx={{ mb: 1, bgcolor: 'grey.100' }}>
                        <CardContent sx={{ py: 1 }}>
                          <Typography variant="body2">{doc.document_number}</Typography>
                          <Typography variant="caption">{doc.title}</Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                )}

                <Card sx={{ bgcolor: 'primary.light', mb: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                      Current Document
                    </Typography>
                    <Typography variant="body1">{genealogy.current_document.document_number}</Typography>
                    <Typography variant="body2">{genealogy.current_document.title}</Typography>
                    <Typography variant="caption">Version: {genealogy.current_document.current_version}</Typography>
                  </CardContent>
                </Card>

                {genealogy.superseded_by.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Superseded By</Typography>
                    {genealogy.superseded_by.map((doc: any) => (
                      <Card key={doc.id} sx={{ mb: 1, bgcolor: 'error.light' }}>
                        <CardContent sx={{ py: 1 }}>
                          <Typography variant="body2">{doc.document_number}</Typography>
                          <Typography variant="caption">{doc.title}</Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                )}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGenealogyDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default DocumentVersionControl