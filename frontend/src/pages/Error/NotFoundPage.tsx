import React from 'react'
import { Box, Typography, Button, Paper } from '@mui/material'
import { Home, ArrowBack } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: 'background.default',
        p: 3,
      }}
    >
      <Paper sx={{ p: 4, textAlign: 'center', maxWidth: 500 }}>
        <Typography variant="h1" sx={{ fontSize: '6rem', fontWeight: 600, color: 'primary.main', mb: 2 }}>
          404
        </Typography>
        <Typography variant="h5" gutterBottom>
          Page Not Found
        </Typography>
        <Typography variant="body1" color="textSecondary" paragraph>
          The page you're looking for doesn't exist in the QMS Platform.
          It may have been moved, deleted, or you entered the wrong URL.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3 }}>
          <Button
            variant="outlined"
            startIcon={<ArrowBack />}
            onClick={() => navigate(-1)}
          >
            Go Back
          </Button>
          <Button
            variant="contained"
            startIcon={<Home />}
            onClick={() => navigate('/dashboard')}
          >
            Home
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}

export default NotFoundPage