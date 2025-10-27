import React, { useEffect } from 'react'
import { Box, Typography, Paper } from '@mui/material'
import { Warning } from '@mui/icons-material'
import { useDispatch } from 'react-redux'
import { setPageTitle, setBreadcrumbs } from '@store/slices/uiSlice'

const QualityPage: React.FC = () => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(setPageTitle('Quality Management'))
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Quality' }
    ]))
  }, [dispatch])

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 3 }}>
        Quality Management System
      </Typography>

      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Warning sx={{ fontSize: 64, color: 'warning.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          Quality Risk Management & CAPA
        </Typography>
        <Typography variant="body1" color="textSecondary" paragraph>
          Manage quality events, conduct risk assessments, and track
          corrective and preventive actions (CAPA) for pharmaceutical compliance.
        </Typography>
        <Typography variant="body2" color="textSecondary">
          ⚠️ Quality Events • 🔍 Risk Assessment • 🔧 CAPA Management • 📊 QRM Analytics
        </Typography>
      </Paper>
    </Box>
  )
}

export default QualityPage