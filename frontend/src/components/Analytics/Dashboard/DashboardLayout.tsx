// Dashboard Layout Component - Phase B Sprint 1 Day 3
// Responsive grid-based dashboard framework with real-time updates

import React, { useState, useEffect } from 'react';
import { Grid, Box, Paper, AppBar, Toolbar, Typography, IconButton } from '@mui/material';
import { Refresh, Settings, Fullscreen, Download } from '@mui/icons-material';

interface DashboardWidget {
  id: string;
  type: 'kpi' | 'chart' | 'table' | 'alert' | 'activity';
  title: string;
  component: React.ComponentType<any>;
  props?: any;
  layout: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  minW?: number;
  minH?: number;
  maxW?: number;
  maxH?: number;
}

interface DashboardLayoutProps {
  title: string;
  widgets: DashboardWidget[];
  isEditable?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onLayoutChange?: (layout: any[]) => void;
  onWidgetUpdate?: (widgetId: string, data: any) => void;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  title,
  widgets,
  isEditable = false,
  autoRefresh = true,
  refreshInterval = 30000,
  onLayoutChange,
  onWidgetUpdate
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(() => {
        setLastRefresh(new Date());
        // Trigger data refresh for all widgets
        widgets.forEach(widget => {
          if (onWidgetUpdate) {
            onWidgetUpdate(widget.id, { forceRefresh: true });
          }
        });
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, widgets, onWidgetUpdate]);

  // Manual refresh
  const handleRefresh = () => {
    setLastRefresh(new Date());
    widgets.forEach(widget => {
      if (onWidgetUpdate) {
        onWidgetUpdate(widget.id, { forceRefresh: true });
      }
    });
  };

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Dashboard Header */}
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {title}
          </Typography>
          <Typography variant="caption" sx={{ mr: 2 }}>
            Last updated: {lastRefresh.toLocaleTimeString()}
          </Typography>
          <IconButton onClick={handleRefresh} title="Refresh Dashboard">
            <Refresh />
          </IconButton>
          <IconButton onClick={toggleFullscreen} title="Fullscreen">
            <Fullscreen />
          </IconButton>
          <IconButton title="Export Dashboard">
            <Download />
          </IconButton>
          {isEditable && (
            <IconButton title="Dashboard Settings">
              <Settings />
            </IconButton>
          )}
        </Toolbar>
      </AppBar>

      {/* Dashboard Content */}
      <Box sx={{ flex: 1, p: 2, overflow: 'auto' }}>
        <Grid container spacing={2}>
          {widgets.map((widget, index) => (
            <Grid 
              item 
              xs={12} 
              sm={widget.layout.w <= 6 ? 6 : 12} 
              md={widget.layout.w <= 4 ? 4 : widget.layout.w <= 6 ? 6 : 12}
              lg={widget.layout.w}
              key={widget.id}
            >
              <Paper 
                elevation={2}
                sx={{ 
                  p: 2, 
                  height: widget.layout.h * 60,
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden'
                }}
              >
                <Typography variant="h6" gutterBottom>
                  {widget.title}
                </Typography>
                <Box sx={{ flex: 1, overflow: 'hidden' }}>
                  <widget.component 
                    {...widget.props}
                    lastRefresh={lastRefresh}
                    onUpdate={(data: any) => onWidgetUpdate?.(widget.id, data)}
                  />
                </Box>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );
};

export default DashboardLayout;