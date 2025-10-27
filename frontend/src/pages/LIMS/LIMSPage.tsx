import React, { useEffect } from 'react'
import { Box, Typography, Paper } from '@mui/material'
import { Science } from '@mui/icons-material'
import { useDispatch } from 'react-redux'
import { setPageTitle, setBreadcrumbs } from '@store/slices/uiSlice'

const LIMSPage: React.FC = () => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(setPageTitle('Laboratory Information Management'))
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'LIMS' }
    ]))
  }, [dispatch])

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 3 }}>
        Laboratory Information Management System
      </Typography>

      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Science sx={{ fontSize: 64, color: 'info.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          LIMS - Laboratory Management
        </Typography>
        <Typography variant="body1" color="textSecondary" paragraph>
          Comprehensive laboratory data management with sample tracking,
          test method management, and analytical data integrity controls.
        </Typography>
        <Typography variant="body2" color="textSecondary">
          🧪 Sample Tracking • 📊 Test Results • 🔬 Method Management • ✅ Data Integrity
        </Typography>
      </Paper>
    </Box>
  )
}

export default LIMSPage