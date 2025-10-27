import React, { useEffect } from 'react'
import { Box, Typography, Paper } from '@mui/material'
import { Settings } from '@mui/icons-material'
import { useDispatch } from 'react-redux'
import { setPageTitle, setBreadcrumbs } from '@store/slices/uiSlice'

const SettingsPage: React.FC = () => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(setPageTitle('System Settings'))
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Settings' }
    ]))
  }, [dispatch])

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 3 }}>
        System Settings
      </Typography>

      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Settings sx={{ fontSize: 64, color: 'action.active', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          System Configuration & Administration
        </Typography>
        <Typography variant="body1" color="textSecondary" paragraph>
          Configure system settings, manage integrations, and
          administer the QMS platform for optimal performance.
        </Typography>
        <Typography variant="body2" color="textSecondary">
          ⚙️ System Config • 🔗 Integrations • 📊 Monitoring • 🔧 Maintenance
        </Typography>
      </Paper>
    </Box>
  )
}

export default SettingsPage