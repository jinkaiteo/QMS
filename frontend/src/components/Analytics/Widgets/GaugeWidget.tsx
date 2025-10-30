// Gauge Widget Component - Phase B Sprint 1 Day 4
// Advanced gauge chart visualization with thresholds and animations

import React, { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';
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