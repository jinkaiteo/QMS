import React from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  LinearProgress,
  useTheme,
} from '@mui/material'
import {
  CheckCircle,
  Warning,
  Error,
  Info,
} from '@mui/icons-material'

interface ModuleStatusCardProps {
  title: string
  description: string
  status: 'healthy' | 'warning' | 'error' | 'info'
  progress?: number
  actionLabel?: string
  onAction?: () => void
  icon?: React.ReactNode
  lastUpdate?: string
}

const ModuleStatusCard: React.FC<ModuleStatusCardProps> = ({
  title,
  description,
  status,
  progress,
  actionLabel = 'View Details',
  onAction,
  icon,
  lastUpdate,
}) => {
  const theme = useTheme()

  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
        return {
          color: 'success',
          bgColor: theme.palette.success.main + '15',
          borderColor: theme.palette.success.main + '30',
          icon: <CheckCircle sx={{ color: 'success.main' }} />,
          label: 'Operational',
        }
      case 'warning':
        return {
          color: 'warning',
          bgColor: theme.palette.warning.main + '15',
          borderColor: theme.palette.warning.main + '30',
          icon: <Warning sx={{ color: 'warning.main' }} />,
          label: 'Attention',
        }
      case 'error':
        return {
          color: 'error',
          bgColor: theme.palette.error.main + '15',
          borderColor: theme.palette.error.main + '30',
          icon: <Error sx={{ color: 'error.main' }} />,
          label: 'Critical',
        }
      default:
        return {
          color: 'info',
          bgColor: theme.palette.info.main + '15',
          borderColor: theme.palette.info.main + '30',
          icon: <Info sx={{ color: 'info.main' }} />,
          label: 'Information',
        }
    }
  }

  const statusConfig = getStatusConfig()

  return (
    <Card 
      sx={{ 
        height: '100%',
        background: statusConfig.bgColor,
        border: `1px solid ${statusConfig.borderColor}`,
        '&:hover': {
          boxShadow: theme.shadows[4],
          transform: 'translateY(-2px)',
          transition: 'all 0.3s ease-in-out',
        },
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {icon || statusConfig.icon}
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {title}
            </Typography>
          </Box>
          <Chip
            label={statusConfig.label}
            size="small"
            color={statusConfig.color as any}
            variant="outlined"
          />
        </Box>

        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
          {description}
        </Typography>

        {progress !== undefined && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="caption" color="textSecondary">
                Progress
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {progress}%
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={progress} 
              color={statusConfig.color as any}
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button
            variant="outlined"
            size="small"
            color={statusConfig.color as any}
            onClick={onAction}
          >
            {actionLabel}
          </Button>
          {lastUpdate && (
            <Typography variant="caption" color="textSecondary">
              {lastUpdate}
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  )
}

export default ModuleStatusCard