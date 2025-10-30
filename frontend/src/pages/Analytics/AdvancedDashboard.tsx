// Advanced Dashboard - Phase B Sprint 1 Day 4
// Showcase dashboard with advanced features and real-time integration

import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  IconButton, 
  Menu, 
  MenuItem, 
  Chip,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Wifi as ConnectedIcon,
  WifiOff as DisconnectedIcon
} from '@mui/icons-material';

import DashboardLayout from '../../components/Analytics/Dashboard/DashboardLayout';
import KPIWidget from '../../components/Analytics/Widgets/KPIWidget';
import ChartWidget from '../../components/Analytics/Widgets/ChartWidget';
import GaugeWidget from '../../components/Analytics/Widgets/GaugeWidget';
import { analyticsWebSocket } from '../../services/websocket/AnalyticsWebSocketService';
import { dashboardExportService } from '../../services/export/DashboardExportService';

const AdvancedDashboard: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const dashboardRef = useRef<HTMLDivElement>(null);

  // WebSocket connection management
  useEffect(() => {
    const connectWebSocket = async () => {
      try {
        await analyticsWebSocket.connect(1, 1); // Mock user and department
        setIsConnected(true);

        // Subscribe to real-time updates
        analyticsWebSocket.subscribe('metric_update', handleMetricUpdate);
        analyticsWebSocket.subscribe('dashboard_refresh', handleDashboardRefresh);
        analyticsWebSocket.subscribe('alert', handleAlert);

      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setIsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      analyticsWebSocket.disconnect();
    };
  }, []);

  // Handle real-time metric updates
  const handleMetricUpdate = (update: any) => {
    console.log('Received metric update:', update);
    setLastUpdate(new Date());
    setNotification('Dashboard updated with new data');
  };

  // Handle dashboard refresh requests
  const handleDashboardRefresh = (update: any) => {
    console.log('Dashboard refresh requested:', update);
    setLastUpdate(new Date());
  };

  // Handle alerts
  const handleAlert = (alert: any) => {
    console.log('Received alert:', alert);
    setNotification(`Alert: ${alert.data.message}`);
  };

  // Export functions
  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenuAnchor(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportMenuAnchor(null);
  };

  const handleExport = async (format: 'pdf' | 'excel' | 'png') => {
    if (!dashboardRef.current) return;

    try {
      const dashboardData = {
        title: 'Advanced Analytics Dashboard',
        widgets: widgets.map(w => ({
          id: w.id,
          title: w.title,
          type: w.type,
          data: w.props?.data || {},
          position: w.layout
        })),
        metadata: {
          generatedAt: new Date().toISOString(),
          generatedBy: 'QMS User',
          department: 'Quality Assurance',
          period: 'Last 30 days'
        }
      };

      switch (format) {
        case 'pdf':
          await dashboardExportService.exportToPDF(dashboardRef.current, dashboardData);
          break;
        case 'excel':
          await dashboardExportService.exportToExcel(dashboardData);
          break;
        case 'png':
          await dashboardExportService.exportToImage(dashboardRef.current, dashboardData, { format: 'png' });
          break;
      }

      setNotification(`Dashboard exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Export failed:', error);
      setNotification('Export failed. Please try again.');
    } finally {
      handleExportClose();
    }
  };

  // Advanced dashboard configuration with new widget types
  const widgets = [
    {
      id: 'overall-quality-gauge',
      type: 'gauge' as const,
      title: 'Overall Quality Score',
      component: GaugeWidget,
      props: {
        data: {
          value: 87.5,
          min: 0,
          max: 100,
          target: 90,
          unit: '%',
          title: 'Quality Score',
          thresholds: {
            excellent: 90,
            good: 75,
            warning: 60
          }
        },
        size: 180,
        animated: true
      },
      layout: { x: 0, y: 0, w: 3, h: 4 }
    },
    {
      id: 'compliance-gauge',
      type: 'gauge' as const,
      title: 'Compliance Rate',
      component: GaugeWidget,
      props: {
        data: {
          value: 94.2,
          min: 0,
          max: 100,
          target: 95,
          unit: '%',
          title: 'Compliance',
          thresholds: {
            excellent: 95,
            good: 85,
            warning: 70
          }
        },
        size: 180,
        animated: true
      },
      layout: { x: 3, y: 0, w: 3, h: 4 }
    },
    {
      id: 'efficiency-gauge',
      type: 'gauge' as const,
      title: 'Process Efficiency',
      component: GaugeWidget,
      props: {
        data: {
          value: 78.3,
          min: 0,
          max: 100,
          target: 85,
          unit: '%',
          title: 'Efficiency',
          thresholds: {
            excellent: 85,
            good: 70,
            warning: 55
          }
        },
        size: 180,
        animated: true
      },
      layout: { x: 6, y: 0, w: 3, h: 4 }
    },
    {
      id: 'real-time-metrics',
      type: 'kpi' as const,
      title: 'Live Quality Events',
      component: KPIWidget,
      props: {
        data: {
          value: 3,
          unit: 'active',
          previousValue: 5,
          target: 2,
          trend: 'down' as const,
          trendPercentage: 40.0,
          status: 'good' as const,
          description: 'Currently active quality events (real-time)'
        }
      },
      layout: { x: 9, y: 0, w: 3, h: 4 }
    },
    {
      id: 'quality-trends-advanced',
      type: 'chart' as const,
      title: 'Quality Metrics Trends (Real-time)',
      component: ChartWidget,
      props: {
        type: 'line',
        height: 300
      },
      layout: { x: 0, y: 4, w: 8, h: 5 }
    },
    {
      id: 'department-performance-advanced',
      type: 'chart' as const,
      title: 'Department Performance Matrix',
      component: ChartWidget,
      props: {
        type: 'bar',
        height: 300
      },
      layout: { x: 8, y: 4, w: 4, h: 5 }
    },
    {
      id: 'training-progress-kpi',
      type: 'kpi' as const,
      title: 'Training Completion (Today)',
      component: KPIWidget,
      props: {
        data: {
          value: 12,
          unit: 'completed',
          previousValue: 8,
          target: 15,
          trend: 'up' as const,
          trendPercentage: 50.0,
          status: 'good' as const,
          description: 'Training sessions completed today'
        }
      },
      layout: { x: 0, y: 9, w: 3, h: 3 }
    },
    {
      id: 'document-efficiency-kpi',
      type: 'kpi' as const,
      title: 'Document Processing',
      component: KPIWidget,
      props: {
        data: {
          value: 2.1,
          unit: 'avg days',
          previousValue: 3.2,
          target: 2.0,
          trend: 'down' as const,
          trendPercentage: 34.4,
          status: 'warning' as const,
          description: 'Average document approval time'
        }
      },
      layout: { x: 3, y: 9, w: 3, h: 3 }
    },
    {
      id: 'compliance-distribution',
      type: 'chart' as const,
      title: 'Compliance Status Distribution',
      component: ChartWidget,
      props: {
        type: 'doughnut',
        height: 200
      },
      layout: { x: 6, y: 9, w: 6, h: 3 }
    }
  ];

  const handleWidgetUpdate = (widgetId: string, data: any) => {
    console.log(`Advanced widget ${widgetId} updated:`, data);
    
    // Track user interactions via WebSocket
    analyticsWebSocket.trackUserInteraction({
      type: 'widget_interaction',
      widget_id: widgetId,
      dashboard_id: 'advanced-dashboard',
      action: 'update',
      metadata: { timestamp: new Date().toISOString() }
    });
  };

  return (
    <Box>
      {/* Advanced Dashboard Header */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        p: 2,
        backgroundColor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider'
      }}>
        <Box>
          <Typography variant="h5" component="h1">
            Advanced Analytics Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time insights with advanced visualizations
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Connection Status */}
          <Chip
            icon={isConnected ? <ConnectedIcon /> : <DisconnectedIcon />}
            label={isConnected ? 'Live' : 'Offline'}
            color={isConnected ? 'success' : 'error'}
            variant="outlined"
            size="small"
          />

          {/* Last Update Time */}
          <Typography variant="caption" color="text.secondary">
            Updated: {lastUpdate.toLocaleTimeString()}
          </Typography>

          {/* Export Button */}
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExportClick}
            size="small"
          >
            Export
          </Button>

          {/* Export Menu */}
          <Menu
            anchorEl={exportMenuAnchor}
            open={Boolean(exportMenuAnchor)}
            onClose={handleExportClose}
          >
            <MenuItem onClick={() => handleExport('pdf')}>
              Export as PDF
            </MenuItem>
            <MenuItem onClick={() => handleExport('excel')}>
              Export as Excel
            </MenuItem>
            <MenuItem onClick={() => handleExport('png')}>
              Export as Image
            </MenuItem>
          </Menu>

          {/* Refresh Button */}
          <IconButton 
            onClick={() => setLastUpdate(new Date())}
            title="Manual Refresh"
          >
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Dashboard Content */}
      <Box ref={dashboardRef}>
        <DashboardLayout
          title=""
          widgets={widgets}
          isEditable={false}
          autoRefresh={isConnected}
          refreshInterval={10000} // 10 seconds for real-time
          onWidgetUpdate={handleWidgetUpdate}
        />
      </Box>

      {/* Notifications */}
      <Snackbar
        open={Boolean(notification)}
        autoHideDuration={4000}
        onClose={() => setNotification(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setNotification(null)} 
          severity="info" 
          variant="filled"
        >
          {notification}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AdvancedDashboard;