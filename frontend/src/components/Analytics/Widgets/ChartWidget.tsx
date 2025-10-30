// Chart Widget Component - Phase B Sprint 1 Day 3
// Interactive chart visualizations using Chart.js

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

  // Generate mock data for demonstration
  useEffect(() => {
    if (!chartData) {
      setTimeout(() => {
        const mockData = generateMockData(chartType);
        setChartData(mockData);
        setIsLoading(false);
      }, 1200);
    }
  }, [chartType]);

  const generateMockData = (type: string): ChartData => {
    const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    
    if (type === 'pie' || type === 'doughnut') {
      return {
        labels: ['Quality Events', 'Training Completed', 'Documents Approved', 'CAPAs Resolved'],
        datasets: [{
          label: 'Distribution',
          data: [25, 35, 20, 20],
          backgroundColor: [
            '#FF6384',
            '#36A2EB', 
            '#FFCE56',
            '#4BC0C0'
          ],
          borderWidth: 2
        }]
      };
    }
    
    return {
      labels,
      datasets: [
        {
          label: 'Current Period',
          data: labels.map(() => Math.floor(Math.random() * 100) + 20),
          backgroundColor: type === 'line' ? 'rgba(54, 162, 235, 0.2)' : 'rgba(54, 162, 235, 0.8)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 2,
          fill: type === 'line'
        },
        {
          label: 'Previous Period',
          data: labels.map(() => Math.floor(Math.random() * 80) + 15),
          backgroundColor: type === 'line' ? 'rgba(255, 99, 132, 0.2)' : 'rgba(255, 99, 132, 0.8)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 2,
          fill: type === 'line'
        }
      ]
    };
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
            onChange={(e) => {
              setChartType(e.target.value as any);
              setIsLoading(true);
              setChartData(null);
            }}
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