import React from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  useTheme,
} from '@mui/material'
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
} from '@mui/icons-material'

interface KPIWidgetProps {
  title: string
  value: number | string
  subtitle?: string
  trend?: 'up' | 'down' | 'flat'
  trendValue?: string
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error'
  icon?: React.ReactNode
}

const KPIWidget: React.FC<KPIWidgetProps> = ({
  title,
  value,
  subtitle,
  trend = 'flat',
  trendValue,
  color = 'primary',
  icon,
}) => {
  const theme = useTheme()

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp sx={{ fontSize: 16, color: 'success.main' }} />
      case 'down':
        return <TrendingDown sx={{ fontSize: 16, color: 'error.main' }} />
      default:
        return <TrendingFlat sx={{ fontSize: 16, color: 'grey.500' }} />
    }
  }

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'success'
      case 'down':
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <Card 
      sx={{ 
        height: '100%',
        background: `linear-gradient(135deg, ${theme.palette[color].main}15, ${theme.palette[color].main}05)`,
        border: `1px solid ${theme.palette[color].main}30`,
        '&:hover': {
          boxShadow: theme.shadows[4],
          transform: 'translateY(-2px)',
          transition: 'all 0.3s ease-in-out',
        },
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="subtitle2" color="textSecondary" sx={{ fontWeight: 500 }}>
            {title}
          </Typography>
          {icon && (
            <Box sx={{ color: `${color}.main`, opacity: 0.7 }}>
              {icon}
            </Box>
          )}
        </Box>

        <Typography 
          variant="h4" 
          sx={{ 
            fontWeight: 'bold', 
            color: `${color}.main`,
            mb: 1,
          }}
        >
          {value}
        </Typography>

        {subtitle && (
          <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
            {subtitle}
          </Typography>
        )}

        {trendValue && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {getTrendIcon()}
            <Chip
              label={trendValue}
              size="small"
              color={getTrendColor() as any}
              variant="outlined"
              sx={{ fontSize: '0.75rem', height: 20 }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

export default KPIWidget