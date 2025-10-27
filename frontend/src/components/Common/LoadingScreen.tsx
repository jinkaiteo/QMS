import React from 'react'
import { Box, CircularProgress, Typography, Paper } from '@mui/material'

interface LoadingScreenProps {
  message?: string
  size?: number
  fullScreen?: boolean
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ 
  message = 'Loading QMS Platform...', 
  size = 40,
  fullScreen = true 
}) => {
  const containerSx = fullScreen 
    ? {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(245, 245, 245, 0.9)',
        zIndex: 9999,
      }
    : {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '200px',
        padding: 3,
      }

  return (
    <Box sx={containerSx}>
      <Paper
        elevation={fullScreen ? 3 : 1}
        sx={{
          padding: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          backgroundColor: 'background.paper',
          borderRadius: 2,
        }}
      >
        <CircularProgress 
          size={size} 
          sx={{ 
            color: 'primary.main',
            marginBottom: 2,
          }} 
        />
        <Typography 
          variant="body1" 
          color="textSecondary"
          sx={{ 
            textAlign: 'center',
            fontWeight: 500,
          }}
        >
          {message}
        </Typography>
        {fullScreen && (
          <Typography 
            variant="caption" 
            color="textSecondary"
            sx={{ 
              marginTop: 1,
              textAlign: 'center',
            }}
          >
            QMS Platform v3.0 - Pharmaceutical Quality Management
          </Typography>
        )}
      </Paper>
    </Box>
  )
}

export default LoadingScreen