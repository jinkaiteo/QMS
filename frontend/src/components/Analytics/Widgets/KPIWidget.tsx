// KPI Widget Component - Phase B Sprint 1 Day 3
// Interactive KPI displays with trends and performance indicators

import React, { useState, useEffect } from 'react';
import { Box, Typography, Chip, IconButton, Skeleton, LinearProgress } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat, Info, TrackChanges as Target } from '@mui/icons-material';

interface KPIData {
  value: number;
  unit: string;
  previousValue?: number;
  target?: number;
  trend: 'up' | 'down' | 'flat';
  trendPercentage?: number;
  status: 'excellent' | 'good' | 'warning' | 'critical';
  description?: string;
}

interface KPIWidgetProps {
  title: string;
  data?: KPIData;
  loading?: boolean;
  lastRefresh?: Date;
  onUpdate?: (data: any) => void;
  apiEndpoint?: string;
}

const KPIWidget: React.FC<KPIWidgetProps> = ({
  title,
  data,
  loading = false,
  lastRefresh,
  onUpdate,
  apiEndpoint
}) => {
  const [kpiData, setKpiData] = useState<KPIData | null>(data || null);
  const [isLoading, setIsLoading] = useState(loading);

  // Mock data for demonstration
  useEffect(() => {
    if (!kpiData) {
      // Simulate API call with mock data
      setTimeout(() => {
        setKpiData({
          value: Math.floor(Math.random() * 100) + 50,
          unit: '%',
          previousValue: Math.floor(Math.random() * 100) + 40,
          target: 85,
          trend: ['up', 'down', 'flat'][Math.floor(Math.random() * 3)] as any,
          trendPercentage: Math.random() * 20,
          status: ['excellent', 'good', 'warning', 'critical'][Math.floor(Math.random() * 4)] as any,
          description: 'This metric shows performance over the selected period'
        });
        setIsLoading(false);
      }, 1000);
    }
  }, []);

  // Get trend icon
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp />;
      case 'down': return <TrendingDown />;
      default: return <TrendingFlat />;
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return '#4caf50';
      case 'good': return '#8bc34a';
      case 'warning': return '#ff9800';
      case 'critical': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  // Format number with proper units
  const formatNumber = (value: number): string => {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
      return (value / 1000).toFixed(1) + 'K';
    }
    return value.toFixed(1);
  };

  if (isLoading || !kpiData) {
    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Skeleton variant="text" width="60%" height={24} />
        <Skeleton variant="text" width="80%" height={48} sx={{ mt: 1 }} />
        <Skeleton variant="rectangular" width="100%" height={40} sx={{ mt: 2 }} />
      </Box>
    );
  }

  const targetProgress = kpiData.target ? (kpiData.value / kpiData.target) * 100 : 0;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* KPI Value */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography 
          variant="h3" 
          component="div"
          sx={{ 
            fontWeight: 'bold',
            color: getStatusColor(kpiData.status),
            flexGrow: 1
          }}
        >
          {formatNumber(kpiData.value)}
          <Typography 
            variant="body2" 
            component="span" 
            sx={{ ml: 1, fontSize: '0.5em', color: 'text.secondary' }}
          >
            {kpiData.unit}
          </Typography>
        </Typography>
        
        {kpiData.description && (
          <IconButton size="small" title={kpiData.description}>
            <Info fontSize="small" />
          </IconButton>
        )}
      </Box>

      {/* Trend Indicator */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <Chip
          icon={getTrendIcon(kpiData.trend)}
          label={
            kpiData.trendPercentage 
              ? `${kpiData.trendPercentage.toFixed(1)}%` 
              : kpiData.trend
          }
          size="small"
          color={kpiData.trend === 'up' ? 'success' : kpiData.trend === 'down' ? 'error' : 'default'}
          variant="outlined"
        />
        <Typography variant="caption" color="text.secondary">
          vs previous period
        </Typography>
      </Box>

      {/* Target Comparison */}
      {kpiData.target && (
        <Box sx={{ mt: 'auto' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Target fontSize="small" />
            <Typography variant="caption" color="text.secondary">
              Target: {formatNumber(kpiData.target)} {kpiData.unit}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={Math.min(targetProgress, 100)}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: '#e0e0e0',
              '& .MuiLinearProgress-bar': {
                backgroundColor: getStatusColor(kpiData.status),
                borderRadius: 4,
              }
            }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            {targetProgress.toFixed(0)}% of target
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default KPIWidget;