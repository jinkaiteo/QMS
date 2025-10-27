import React, { useEffect } from 'react'
import { Box, Typography, Paper } from '@mui/material'
import { People } from '@mui/icons-material'
import { useDispatch } from 'react-redux'
import { setPageTitle, setBreadcrumbs } from '@store/slices/uiSlice'

const UsersPage: React.FC = () => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(setPageTitle('User Management'))
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Users' }
    ]))
  }, [dispatch])

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 3 }}>
        User Management
      </Typography>

      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <People sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          User Administration & Access Control
        </Typography>
        <Typography variant="body1" color="textSecondary" paragraph>
          Manage user accounts, roles, permissions, and access controls
          for the pharmaceutical quality management system.
        </Typography>
        <Typography variant="body2" color="textSecondary">
          👥 User Accounts • 🔐 Role Management • 🛡️ Permissions • 📊 Access Logs
        </Typography>
      </Paper>
    </Box>
  )
}

export default UsersPage