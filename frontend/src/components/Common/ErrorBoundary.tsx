import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Box, Paper, Typography, Button, Alert, Divider } from '@mui/material'
import { ErrorOutline, Refresh, BugReport } from '@mui/icons-material'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null 
    }
  }

  public static getDerivedStateFromError(error: Error): State {
    return { 
      hasError: true, 
      error, 
      errorInfo: null 
    }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('QMS Platform Error Boundary caught an error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo
    })

    // In a real application, you would send this to your error reporting service
    // Example: Sentry, LogRocket, etc.
    this.reportError(error, errorInfo)
  }

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    // Report to error monitoring service
    console.error('Error reported:', {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    })
  }

  private handleReload = () => {
    window.location.reload()
  }

  private handleReset = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    })
  }

  public render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            backgroundColor: 'background.default',
            padding: 3,
          }}
        >
          <Paper
            elevation={3}
            sx={{
              padding: 4,
              maxWidth: 600,
              width: '100%',
              textAlign: 'center',
            }}
          >
            <Box sx={{ mb: 3 }}>
              <ErrorOutline 
                sx={{ 
                  fontSize: 64, 
                  color: 'error.main',
                  mb: 2 
                }} 
              />
              <Typography variant="h4" color="error" gutterBottom>
                Oops! Something went wrong
              </Typography>
              <Typography variant="body1" color="textSecondary" paragraph>
                We're sorry, but something unexpected happened in the QMS Platform. 
                Our team has been notified and is working to fix this issue.
              </Typography>
            </Box>

            <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
              <Typography variant="subtitle2" gutterBottom>
                Error Details:
              </Typography>
              <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem' }}>
                {this.state.error?.message}
              </Typography>
            </Alert>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mb: 3 }}>
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={this.handleReload}
                color="primary"
              >
                Reload Page
              </Button>
              <Button
                variant="outlined"
                onClick={this.handleReset}
                color="primary"
              >
                Try Again
              </Button>
            </Box>

            <Divider sx={{ mb: 2 }} />

            <Typography variant="caption" color="textSecondary">
              If this problem persists, please contact your system administrator.
            </Typography>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <Box sx={{ mt: 3, textAlign: 'left' }}>
                <Typography variant="subtitle2" gutterBottom>
                  <BugReport sx={{ verticalAlign: 'middle', mr: 1 }} />
                  Development Error Details:
                </Typography>
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 2, 
                    backgroundColor: 'grey.50',
                    overflow: 'auto',
                    maxHeight: 200,
                  }}
                >
                  <Typography 
                    variant="body2" 
                    component="pre" 
                    sx={{ 
                      fontSize: '0.7rem',
                      fontFamily: 'monospace',
                      margin: 0,
                    }}
                  >
                    {this.state.error?.stack}
                    {'\n\nComponent Stack:'}
                    {this.state.errorInfo.componentStack}
                  </Typography>
                </Paper>
              </Box>
            )}
          </Paper>
        </Box>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary