# 🎨 Phase B Sprint 1 Day 3 - Dashboard Framework & Visualization

**Phase**: B - Advanced Reporting & Analytics  
**Sprint**: 1 - Analytics Foundation & Data Model  
**Day**: 3 - Dashboard Framework & Visualization  
**Focus**: Creating interactive dashboards and data visualization components

---

## 🎯 **Day 3 Objectives**

### **Primary Goals:**
- [ ] Build responsive dashboard framework with Material-UI
- [ ] Create interactive chart components using Chart.js and D3.js
- [ ] Implement KPI widgets and performance indicators
- [ ] Connect dashboards to analytics APIs for real-time data
- [ ] Design executive, quality, training, and departmental dashboards
- [ ] Optimize performance for large datasets and real-time updates

### **Deliverables:**
- Dashboard framework with grid layout system
- Chart component library (Line, Bar, Pie, Gauge, Heatmap)
- KPI widget components with trend indicators
- Real-time data integration layer
- Multiple dashboard templates (Executive, Quality, Training, Department)
- Mobile-responsive design with touch interactions

---

## 🎨 **Dashboard Architecture Design**

### **Component Hierarchy:**
```
AnalyticsDashboard
├── DashboardLayout (Grid System)
│   ├── DashboardHeader (Title, Controls, Refresh)
│   ├── DashboardFilters (Department, Date Range, Modules)
│   └── DashboardGrid (Responsive Widget Container)
│       ├── KPIWidget (Metrics with Trends)
│       ├── ChartWidget (Interactive Visualizations)
│       ├── TableWidget (Detailed Data Tables)
│       ├── AlertWidget (Notifications & Warnings)
│       └── ActivityWidget (Recent Events Feed)
├── DashboardControls
│   ├── WidgetPicker (Add/Remove Widgets)
│   ├── LayoutManager (Drag & Drop Positioning)
│   └── ExportControls (PDF, Excel, Image Export)
└── RealTimeDataProvider (WebSocket/Polling Integration)
```

### **Dashboard Types:**
- **📊 Executive Dashboard**: High-level KPIs and organizational overview
- **🏥 Quality Dashboard**: Quality metrics, CAPA effectiveness, compliance
- **🎓 Training Dashboard**: Completion rates, compliance, performance
- **🏢 Department Dashboard**: Department-specific metrics and comparisons
- **📱 Mobile Dashboard**: Touch-optimized mobile interface
- **🎯 Personal Dashboard**: User-specific metrics and tasks

---

## 🛠️ **Frontend Implementation**

### **1. Dashboard Framework Foundation**

#### **Dashboard Layout System**
```typescript
// frontend/src/components/Analytics/Dashboard/DashboardLayout.tsx
import React, { useState, useEffect } from 'react';
import { Grid, Box, Paper, AppBar, Toolbar, Typography, IconButton } from '@mui/material';
import { Refresh, Settings, Fullscreen, Download } from '@mui/icons-material';
import { Responsive, WidthProvider } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

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
  const [layouts, setLayouts] = useState<any>({});
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

  // Layout management
  const handleLayoutChange = (layout: any[], layouts: any) => {
    setLayouts(layouts);
    if (onLayoutChange) {
      onLayoutChange(layout);
    }
  };

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

  // Convert widgets to grid layout format
  const gridLayouts = {
    lg: widgets.map(widget => ({
      i: widget.id,
      x: widget.layout.x,
      y: widget.layout.y,
      w: widget.layout.w,
      h: widget.layout.h,
      minW: widget.minW || 2,
      minH: widget.minH || 2,
      maxW: widget.maxW || 12,
      maxH: widget.maxH || 8
    }))
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
        <ResponsiveGridLayout
          className="dashboard-grid"
          layouts={layouts.lg ? layouts : gridLayouts}
          onLayoutChange={handleLayoutChange}
          isDraggable={isEditable}
          isResizable={isEditable}
          compactType="vertical"
          preventCollision={false}
          margin={[16, 16]}
          containerPadding={[0, 0]}
          rowHeight={60}
          breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
          cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        >
          {widgets.map(widget => (
            <Paper 
              key={widget.id} 
              elevation={2}
              sx={{ 
                p: 2, 
                height: '100%',
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
          ))}
        </ResponsiveGridLayout>
      </Box>
    </Box>
  );
};

export default DashboardLayout;
```

#### **KPI Widget Component**
```typescript
// frontend/src/components/Analytics/Widgets/KPIWidget.tsx
import React, { useState, useEffect } from 'react';
import { Box, Typography, Chip, IconButton, Skeleton } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat, Info } from '@mui/icons-material';
import { formatNumber, formatPercentage, getColorFromValue } from '../../../utils/formatters';

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

  // Fetch data when component mounts or refreshes
  useEffect(() => {
    if (apiEndpoint && (!kpiData || lastRefresh)) {
      fetchKPIData();
    }
  }, [apiEndpoint, lastRefresh]);

  const fetchKPIData = async () => {
    if (!apiEndpoint) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(apiEndpoint);
      const result = await response.json();
      setKpiData(result);
      if (onUpdate) {
        onUpdate(result);
      }
    } catch (error) {
      console.error('Error fetching KPI data:', error);
    } finally {
      setIsLoading(false);
    }
  };

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

  if (isLoading || !kpiData) {
    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Skeleton variant="text" width="60%" height={24} />
        <Skeleton variant="text" width="80%" height={48} sx={{ mt: 1 }} />
        <Skeleton variant="rectangular" width="100%" height={40} sx={{ mt: 2 }} />
      </Box>
    );
  }

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
              ? `${formatPercentage(Math.abs(kpiData.trendPercentage))}` 
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
          <Typography variant="caption" color="text.secondary">
            Target: {formatNumber(kpiData.target)} {kpiData.unit}
          </Typography>
          <Box
            sx={{
              width: '100%',
              height: 8,
              backgroundColor: '#e0e0e0',
              borderRadius: 4,
              mt: 0.5,
              overflow: 'hidden'
            }}
          >
            <Box
              sx={{
                width: `${Math.min((kpiData.value / kpiData.target) * 100, 100)}%`,
                height: '100%',
                backgroundColor: getStatusColor(kpiData.status),
                transition: 'width 0.3s ease'
              }}
            />
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default KPIWidget;
```

#### **Chart Widget Component**
```typescript
// frontend/src/components/Analytics/Widgets/ChartWidget.tsx
import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, CircularProgress, FormControl, Select, MenuItem } from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
    fill?: boolean;
  }[];
}

interface ChartWidgetProps {
  title: string;
  type: 'line' | 'bar' | 'pie' | 'doughnut';
  data?: ChartData;
  loading?: boolean;
  lastRefresh?: Date;
  onUpdate?: (data: any) => void;
  apiEndpoint?: string;
  height?: number;
  options?: any;
}

const ChartWidget: React.FC<ChartWidgetProps> = ({
  title,
  type,
  data,
  loading = false,
  lastRefresh,
  onUpdate,
  apiEndpoint,
  height = 300,
  options = {}
}) => {
  const [chartData, setChartData] = useState<ChartData | null>(data || null);
  const [isLoading, setIsLoading] = useState(loading);
  const [chartType, setChartType] = useState(type);
  const chartRef = useRef<any>(null);

  // Fetch data when component mounts or refreshes
  useEffect(() => {
    if (apiEndpoint && (!chartData || lastRefresh)) {
      fetchChartData();
    }
  }, [apiEndpoint, lastRefresh]);

  const fetchChartData = async () => {
    if (!apiEndpoint) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(apiEndpoint);
      const result = await response.json();
      setChartData(result);
      if (onUpdate) {
        onUpdate(result);
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Default chart options
  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: type === 'line' || type === 'bar' ? {
      x: {
        display: true,
        title: {
          display: false,
        },
      },
      y: {
        display: true,
        title: {
          display: false,
        },
        beginAtZero: true,
      },
    } : {},
    ...options
  };

  // Render appropriate chart type
  const renderChart = () => {
    if (!chartData) return null;

    const chartProps = {
      ref: chartRef,
      data: chartData,
      options: defaultOptions
    };

    switch (chartType) {
      case 'line':
        return <Line {...chartProps} />;
      case 'bar':
        return <Bar {...chartProps} />;
      case 'pie':
        return <Pie {...chartProps} />;
      case 'doughnut':
        return <Doughnut {...chartProps} />;
      default:
        return <Line {...chartProps} />;
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Chart Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="h6" component="h3">
          {title}
        </Typography>
        <FormControl size="small" sx={{ minWidth: 100 }}>
          <Select
            value={chartType}
            onChange={(e) => setChartType(e.target.value as any)}
            variant="outlined"
          >
            <MenuItem value="line">Line</MenuItem>
            <MenuItem value="bar">Bar</MenuItem>
            <MenuItem value="pie">Pie</MenuItem>
            <MenuItem value="doughnut">Doughnut</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Chart Content */}
      <Box sx={{ flex: 1, position: 'relative', minHeight: height }}>
        {isLoading ? (
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              height: '100%'
            }}
          >
            <CircularProgress />
          </Box>
        ) : chartData ? (
          renderChart()
        ) : (
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              height: '100%',
              color: 'text.secondary'
            }}
          >
            <Typography>No data available</Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default ChartWidget;
```

Let me continue with more dashboard components and the integration layer...