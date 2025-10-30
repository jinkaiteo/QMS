# 🚀 Phase B Sprint 1 Day 4 - Advanced Features & Integration

**Phase**: B - Advanced Reporting & Analytics  
**Sprint**: 1 - Analytics Foundation & Data Model  
**Day**: 4 - Advanced Features & Integration  
**Focus**: Advanced visualizations, real-time streaming, export capabilities, and dashboard customization

---

## 🎯 **Day 4 Objectives**

### **Primary Goals:**
- [ ] Implement advanced chart types (Heatmaps, Gauge, Scatter, Treemap)
- [ ] Build real-time WebSocket integration for live data streaming
- [ ] Create PDF/Excel/Image export functionality
- [ ] Develop custom dashboard builder with drag-and-drop
- [ ] Add performance optimization for large datasets
- [ ] Implement dashboard personalization and saving

### **Deliverables:**
- Advanced chart widget library with 6+ new chart types
- Real-time WebSocket service for live data streaming
- Export service with multiple format support
- Dashboard builder interface with customization tools
- Performance optimization for handling 10,000+ data points
- User preference system for dashboard customization

---

## 🎨 **Advanced Visualization Components**

### **1. Advanced Chart Widget Library**

#### **Gauge Chart Component**
```typescript
// frontend/src/components/Analytics/Widgets/GaugeWidget.tsx
import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, FormControl, Select, MenuItem } from '@mui/material';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

interface GaugeData {
  value: number;
  min: number;
  max: number;
  target?: number;
  unit: string;
  title: string;
  thresholds: {
    excellent: number;
    good: number;
    warning: number;
  };
}

interface GaugeWidgetProps {
  data: GaugeData;
  size?: number;
  showTarget?: boolean;
  animated?: boolean;
}

const GaugeWidget: React.FC<GaugeWidgetProps> = ({
  data,
  size = 200,
  showTarget = true,
  animated = true
}) => {
  const [animatedValue, setAnimatedValue] = useState(0);
  
  // Animate gauge value
  useEffect(() => {
    if (animated) {
      const duration = 1500; // 1.5 seconds
      const steps = 60;
      const stepValue = data.value / steps;
      const stepDuration = duration / steps;
      
      let currentStep = 0;
      const timer = setInterval(() => {
        currentStep++;
        setAnimatedValue(stepValue * currentStep);
        
        if (currentStep >= steps) {
          setAnimatedValue(data.value);
          clearInterval(timer);
        }
      }, stepDuration);
      
      return () => clearInterval(timer);
    } else {
      setAnimatedValue(data.value);
    }
  }, [data.value, animated]);

  // Calculate gauge segments
  const range = data.max - data.min;
  const valuePercentage = ((animatedValue - data.min) / range) * 180; // 180 degrees for semicircle
  
  // Color based on thresholds
  const getValueColor = (value: number) => {
    if (value >= data.thresholds.excellent) return '#4caf50';
    if (value >= data.thresholds.good) return '#8bc34a';
    if (value >= data.thresholds.warning) return '#ff9800';
    return '#f44336';
  };

  // Create gauge chart data
  const chartData = {
    datasets: [{
      data: [valuePercentage, 180 - valuePercentage],
      backgroundColor: [
        getValueColor(animatedValue),
        '#e0e0e0'
      ],
      borderWidth: 0,
      cutout: '80%',
      circumference: 180,
      rotation: 270
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        enabled: false
      }
    }
  };

  return (
    <Box sx={{ 
      position: 'relative', 
      width: size, 
      height: size * 0.6,
      mx: 'auto'
    }}>
      {/* Gauge Chart */}
      <Box sx={{ position: 'relative', height: '100%' }}>
        <Doughnut data={chartData} options={chartOptions} />
        
        {/* Center Value Display */}
        <Box sx={{
          position: 'absolute',
          top: '70%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center'
        }}>
          <Typography 
            variant="h4" 
            component="div" 
            sx={{ 
              fontWeight: 'bold',
              color: getValueColor(animatedValue),
              lineHeight: 1
            }}
          >
            {animatedValue.toFixed(1)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {data.unit}
          </Typography>
        </Box>

        {/* Target Indicator */}
        {showTarget && data.target && (
          <Box sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            mt: 3
          }}>
            <Typography variant="caption" color="text.secondary">
              Target: {data.target} {data.unit}
            </Typography>
          </Box>
        )}
      </Box>

      {/* Scale Labels */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between',
        mt: 1,
        px: 2
      }}>
        <Typography variant="caption" color="text.secondary">
          {data.min}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {data.max}
        </Typography>
      </Box>
    </Box>
  );
};

export default GaugeWidget;
```

#### **Heatmap Chart Component**
```typescript
// frontend/src/components/Analytics/Widgets/HeatmapWidget.tsx
import React, { useEffect, useRef } from 'react';
import { Box, Typography } from '@mui/material';
import * as d3 from 'd3';

interface HeatmapData {
  x: string;
  y: string;
  value: number;
}

interface HeatmapWidgetProps {
  data: HeatmapData[];
  title: string;
  width?: number;
  height?: number;
  colorScheme?: string;
}

const HeatmapWidget: React.FC<HeatmapWidgetProps> = ({
  data,
  title,
  width = 600,
  height = 400,
  colorScheme = 'RdYlBu'
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!data.length || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous render

    const margin = { top: 50, right: 30, bottom: 50, left: 100 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Get unique x and y values
    const xValues = Array.from(new Set(data.map(d => d.x)));
    const yValues = Array.from(new Set(data.map(d => d.y)));

    // Create scales
    const xScale = d3.scaleBand()
      .domain(xValues)
      .range([0, innerWidth])
      .padding(0.1);

    const yScale = d3.scaleBand()
      .domain(yValues)
      .range([0, innerHeight])
      .padding(0.1);

    const colorScale = d3.scaleSequential()
      .interpolator(d3.interpolateRdYlBu)
      .domain(d3.extent(data, d => d.value) as [number, number]);

    // Create main group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create heatmap rectangles
    g.selectAll('.heatmap-rect')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'heatmap-rect')
      .attr('x', d => xScale(d.x) || 0)
      .attr('y', d => yScale(d.y) || 0)
      .attr('width', xScale.bandwidth())
      .attr('height', yScale.bandwidth())
      .attr('fill', d => colorScale(d.value))
      .attr('rx', 2)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
        // Tooltip
        d3.select('body')
          .append('div')
          .attr('class', 'heatmap-tooltip')
          .style('position', 'absolute')
          .style('background', 'rgba(0,0,0,0.8)')
          .style('color', 'white')
          .style('padding', '8px')
          .style('border-radius', '4px')
          .style('font-size', '12px')
          .style('pointer-events', 'none')
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px')
          .html(`${d.x} - ${d.y}<br/>Value: ${d.value.toFixed(2)}`);
      })
      .on('mouseout', function() {
        d3.selectAll('.heatmap-tooltip').remove();
      });

    // Add x-axis
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale))
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-45)');

    // Add y-axis
    g.append('g')
      .call(d3.axisLeft(yScale));

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 25)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .text(title);

  }, [data, width, height, title, colorScheme]);

  return (
    <Box sx={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
      />
    </Box>
  );
};

export default HeatmapWidget;
```

#### **Scatter Plot Component**
```typescript
// frontend/src/components/Analytics/Widgets/ScatterPlotWidget.tsx
import React, { useState, useEffect } from 'react';
import { Box, Typography, FormControl, Select, MenuItem, Chip } from '@mui/material';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  ScatterController
} from 'chart.js';
import { Scatter } from 'react-chartjs-2';

ChartJS.register(LinearScale, PointElement, LineElement, Tooltip, Legend, ScatterController);

interface ScatterPoint {
  x: number;
  y: number;
  label?: string;
  category?: string;
}

interface ScatterPlotData {
  datasets: {
    label: string;
    data: ScatterPoint[];
    backgroundColor: string;
    borderColor: string;
  }[];
}

interface ScatterPlotWidgetProps {
  data: ScatterPlotData;
  title: string;
  xAxisLabel: string;
  yAxisLabel: string;
  showTrendLine?: boolean;
  enableZoom?: boolean;
}

const ScatterPlotWidget: React.FC<ScatterPlotWidgetProps> = ({
  data,
  title,
  xAxisLabel,
  yAxisLabel,
  showTrendLine = false,
  enableZoom = true
}) => {
  const [filteredData, setFilteredData] = useState<ScatterPlotData>(data);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Calculate trend line if needed
  const calculateTrendLine = (points: ScatterPoint[]) => {
    if (points.length < 2) return null;

    const n = points.length;
    const sumX = points.reduce((sum, p) => sum + p.x, 0);
    const sumY = points.reduce((sum, p) => sum + p.y, 0);
    const sumXY = points.reduce((sum, p) => sum + p.x * p.y, 0);
    const sumXX = points.reduce((sum, p) => sum + p.x * p.x, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    const minX = Math.min(...points.map(p => p.x));
    const maxX = Math.max(...points.map(p => p.x));

    return [
      { x: minX, y: slope * minX + intercept },
      { x: maxX, y: slope * maxX + intercept }
    ];
  };

  // Chart options
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const point = context.raw as ScatterPoint;
            return `${context.dataset.label}: (${point.x}, ${point.y})${point.label ? ` - ${point.label}` : ''}`;
          }
        }
      },
      zoom: enableZoom ? {
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true
          },
          mode: 'xy' as const,
        },
        pan: {
          enabled: true,
          mode: 'xy' as const,
        }
      } : undefined
    },
    scales: {
      x: {
        type: 'linear' as const,
        position: 'bottom' as const,
        title: {
          display: true,
          text: xAxisLabel
        }
      },
      y: {
        type: 'linear' as const,
        title: {
          display: true,
          text: yAxisLabel
        }
      }
    },
    interaction: {
      intersect: false,
    }
  };

  // Prepare chart data with trend line
  const chartData = {
    datasets: [
      ...filteredData.datasets,
      ...(showTrendLine ? filteredData.datasets.map(dataset => {
        const trendLine = calculateTrendLine(dataset.data);
        return trendLine ? {
          label: `${dataset.label} Trend`,
          data: trendLine,
          type: 'line' as const,
          borderColor: dataset.borderColor,
          backgroundColor: 'transparent',
          borderDash: [5, 5],
          pointRadius: 0,
          pointHoverRadius: 0,
        } : null;
      }).filter(Boolean) : [])
    ]
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header with controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">{title}</Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {showTrendLine && (
            <Chip label="Trend Line" size="small" variant="outlined" />
          )}
          {enableZoom && (
            <Chip label="Zoom Enabled" size="small" variant="outlined" />
          )}
        </Box>
      </Box>

      {/* Chart */}
      <Box sx={{ flex: 1, minHeight: 300 }}>
        <Scatter data={chartData} options={options} />
      </Box>
    </Box>
  );
};

export default ScatterPlotWidget;
```

---

## 🔄 **Real-time WebSocket Integration**

### **WebSocket Service Layer**
```typescript
// frontend/src/services/websocket/AnalyticsWebSocketService.ts
import { io, Socket } from 'socket.io-client';

interface AnalyticsUpdate {
  type: 'metric_update' | 'dashboard_refresh' | 'alert' | 'user_activity';
  data: any;
  timestamp: string;
  department_id?: number;
  user_id?: number;
}

class AnalyticsWebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private listeners: Map<string, Function[]> = new Map();

  constructor(private baseUrl: string = 'ws://localhost:8001') {}

  connect(userId: number, departmentId?: number): Promise<boolean> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = io(this.baseUrl, {
          query: {
            userId,
            departmentId: departmentId || '',
            room: 'analytics'
          },
          transports: ['websocket'],
          reconnection: true,
          reconnectionAttempts: this.maxReconnectAttempts,
          reconnectionDelay: 1000,
        });

        this.socket.on('connect', () => {
          console.log('✅ Analytics WebSocket connected');
          this.reconnectAttempts = 0;
          resolve(true);
        });

        this.socket.on('disconnect', () => {
          console.log('⚠️ Analytics WebSocket disconnected');
        });

        this.socket.on('reconnect', (attemptNumber: number) => {
          console.log(`🔄 Analytics WebSocket reconnected (attempt ${attemptNumber})`);
        });

        this.socket.on('analytics_update', (update: AnalyticsUpdate) => {
          this.handleAnalyticsUpdate(update);
        });

        this.socket.on('connect_error', (error: Error) => {
          console.error('❌ Analytics WebSocket connection error:', error);
          reject(error);
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // Subscribe to specific analytics updates
  subscribe(eventType: string, callback: Function): void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType)?.push(callback);
  }

  // Unsubscribe from analytics updates
  unsubscribe(eventType: string, callback: Function): void {
    const eventListeners = this.listeners.get(eventType);
    if (eventListeners) {
      const index = eventListeners.indexOf(callback);
      if (index > -1) {
        eventListeners.splice(index, 1);
      }
    }
  }

  // Handle incoming analytics updates
  private handleAnalyticsUpdate(update: AnalyticsUpdate): void {
    const listeners = this.listeners.get(update.type) || [];
    listeners.forEach(callback => {
      try {
        callback(update);
      } catch (error) {
        console.error('Error in analytics update callback:', error);
      }
    });

    // Also trigger generic 'update' listeners
    const genericListeners = this.listeners.get('update') || [];
    genericListeners.forEach(callback => {
      try {
        callback(update);
      } catch (error) {
        console.error('Error in generic update callback:', error);
      }
    });
  }

  // Request specific dashboard refresh
  requestDashboardRefresh(dashboardId: string, filters?: any): void {
    if (this.socket?.connected) {
      this.socket.emit('request_dashboard_refresh', {
        dashboardId,
        filters,
        timestamp: new Date().toISOString()
      });
    }
  }

  // Send user interaction events
  trackUserInteraction(interaction: {
    type: string;
    widget_id?: string;
    dashboard_id?: string;
    action?: string;
    metadata?: any;
  }): void {
    if (this.socket?.connected) {
      this.socket.emit('user_interaction', {
        ...interaction,
        timestamp: new Date().toISOString()
      });
    }
  }

  // Get connection status
  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

// Global instance
export const analyticsWebSocket = new AnalyticsWebSocketService();
export default AnalyticsWebSocketService;
```

---

## 📤 **Export Service Implementation**

Let me continue with the export functionality and dashboard builder...