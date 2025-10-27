import React, { useState } from 'react'
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  FormControlLabel,
  Checkbox,
  Divider,
  Link,
  IconButton,
} from '@mui/material'
import { Lock, Person, Visibility, VisibilityOff } from '@mui/icons-material'
import { useForm, Controller } from 'react-hook-form'
import { yupResolver } from '@hookform/resolvers/yup'
import * as yup from 'yup'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'

import { RootState, loginStart, loginSuccess, loginFailure } from '@store/store'
import { addNotification } from '@store/slices/uiSlice'
import { authService } from '@services/authService'
import { LoginCredentials } from '@types/auth'

const loginSchema = yup.object({
  username: yup
    .string()
    .required('Username is required')
    .min(3, 'Username must be at least 3 characters'),
  password: yup
    .string()
    .required('Password is required')
    .min(6, 'Password must be at least 6 characters'),
  remember_me: yup.boolean(),
})

const LoginPage: React.FC = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { isLoading, error } = useSelector((state: RootState) => state.auth)
  
  const [showPassword, setShowPassword] = useState(false)

  const {
    control,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<LoginCredentials>({
    resolver: yupResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
      remember_me: false,
    },
  })

  const onSubmit = async (data: LoginCredentials) => {
    try {
      console.log('Starting login with data:', data)
      dispatch(loginStart())
      
      // Call auth service directly
      const response = await authService.login(data)
      console.log('Auth service response:', response)
      
      // Dispatch success action to simple store
      dispatch(loginSuccess({
        user: response.user,
        token: response.access_token
      }))
      
      const userName = response.user?.full_name || response.user?.username || 'User'
      
      dispatch(addNotification({
        type: 'success',
        title: 'Login Successful',
        message: `Welcome back, ${userName}!`,
      }))
      
      console.log('Login successful, navigating to dashboard')
      navigate('/dashboard')
      
    } catch (error: any) {
      console.error('Login error:', error)
      dispatch(loginFailure())
      
      const errorMessage = error.message || 'Login failed'
      setError('root', { message: errorMessage })
      
      dispatch(addNotification({
        type: 'error',
        title: 'Login Failed',
        message: errorMessage,
      }))
    }
  }

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'background.default',
        backgroundImage: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: 3,
      }}
    >
      <Paper
        elevation={8}
        sx={{
          padding: 4,
          width: '100%',
          maxWidth: 400,
          borderRadius: 2,
          backgroundColor: 'background.paper',
        }}
      >
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 60,
              height: 60,
              borderRadius: '50%',
              backgroundColor: 'primary.main',
              mb: 2,
            }}
          >
            <Lock sx={{ fontSize: 30, color: 'white' }} />
          </Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
            QMS Platform
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Pharmaceutical Quality Management System
          </Typography>
          <Typography variant="caption" color="textSecondary" display="block" sx={{ mt: 1 }}>
            21 CFR Part 11 Compliant • Version 3.0
          </Typography>
        </Box>

        {/* Error Alert */}
        {(error || errors.root) && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error || errors.root?.message}
          </Alert>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit(onSubmit)}>
          <Box sx={{ mb: 3 }}>
            <Controller
              name="username"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Username"
                  variant="outlined"
                  error={!!errors.username}
                  helperText={errors.username?.message}
                  InputProps={{
                    startAdornment: <Person sx={{ mr: 1, color: 'action.active' }} />,
                  }}
                  autoComplete="username"
                  autoFocus
                />
              )}
            />
          </Box>

          <Box sx={{ mb: 3 }}>
            <Controller
              name="password"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  variant="outlined"
                  error={!!errors.password}
                  helperText={errors.password?.message}
                  InputProps={{
                    startAdornment: <Lock sx={{ mr: 1, color: 'action.active' }} />,
                    endAdornment: (
                      <IconButton
                        onClick={handleTogglePasswordVisibility}
                        edge="end"
                        aria-label="toggle password visibility"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    ),
                  }}
                  autoComplete="current-password"
                />
              )}
            />
          </Box>

          <Box sx={{ mb: 3 }}>
            <Controller
              name="remember_me"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={<Checkbox {...field} checked={field.value} />}
                  label="Remember me"
                />
              )}
            />
          </Box>

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={isLoading}
            sx={{
              mb: 3,
              height: 48,
              fontSize: '1rem',
              fontWeight: 600,
            }}
          >
            {isLoading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              'Sign In'
            )}
          </Button>
        </form>

        <Divider sx={{ mb: 3 }} />

        {/* Footer Links */}
        <Box sx={{ textAlign: 'center' }}>
          <Link
            href="#"
            variant="body2"
            sx={{ display: 'block', mb: 1 }}
            onClick={(e) => {
              e.preventDefault()
              dispatch(addNotification({
                type: 'info',
                title: 'Password Reset',
                message: 'Please contact your system administrator for password reset.',
              }))
            }}
          >
            Forgot password?
          </Link>
          <Typography variant="caption" color="textSecondary">
            Need help? Contact your system administrator
          </Typography>
        </Box>

        {/* Demo Credentials (Development only) */}
        {process.env.NODE_ENV === 'development' && (
          <Box sx={{ mt: 3, p: 2, backgroundColor: 'info.main', borderRadius: 1 }}>
            <Typography variant="caption" sx={{ color: 'info.contrastText', display: 'block', mb: 1 }}>
              Demo Credentials:
            </Typography>
            <Typography variant="caption" sx={{ color: 'info.contrastText', display: 'block' }}>
              Username: admin / Password: admin123
            </Typography>
            <Typography variant="caption" sx={{ color: 'info.contrastText', display: 'block' }}>
              Username: user / Password: user123
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  )
}

export default LoginPage