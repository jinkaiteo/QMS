// Training Dashboard - Phase B Sprint 1 Day 3
// Training-focused dashboard for training managers and HR teams

import React from 'react';
import DashboardLayout from '../../components/Analytics/Dashboard/DashboardLayout';
import KPIWidget from '../../components/Analytics/Widgets/KPIWidget';
import ChartWidget from '../../components/Analytics/Widgets/ChartWidget';

const TrainingDashboard: React.FC = () => {
  // Training-focused dashboard configuration
  const widgets = [
    {
      id: 'completion-rate',
      type: 'kpi' as const,
      title: 'Overall Completion Rate',
      component: KPIWidget,
      props: {
        data: {
          value: 92.3,
          unit: '%',
          previousValue: 89.1,
          target: 95,
          trend: 'up' as const,
          trendPercentage: 3.6,
          status: 'good' as const,
          description: 'Percentage of assigned training completed'
        }
      },
      layout: { x: 0, y: 0, w: 3, h: 3 }
    },
    {
      id: 'overdue-training',
      type: 'kpi' as const,
      title: 'Overdue Training',
      component: KPIWidget,
      props: {
        data: {
          value: 23,
          unit: 'items',
          previousValue: 31,
          target: 15,
          trend: 'down' as const,
          trendPercentage: 25.8,
          status: 'warning' as const,
          description: 'Number of overdue training assignments'
        }
      },
      layout: { x: 3, y: 0, w: 3, h: 3 }
    },
    {
      id: 'avg-score',
      type: 'kpi' as const,
      title: 'Average Training Score',
      component: KPIWidget,
      props: {
        data: {
          value: 88.7,
          unit: '%',
          previousValue: 86.2,
          target: 85,
          trend: 'up' as const,
          trendPercentage: 2.9,
          status: 'excellent' as const,
          description: 'Average score across all completed training'
        }
      },
      layout: { x: 6, y: 0, w: 3, h: 3 }
    },
    {
      id: 'hours-completed',
      type: 'kpi' as const,
      title: 'Training Hours (Monthly)',
      component: KPIWidget,
      props: {
        data: {
          value: 1247,
          unit: 'hours',
          previousValue: 1156,
          target: 1200,
          trend: 'up' as const,
          trendPercentage: 7.9,
          status: 'excellent' as const,
          description: 'Total training hours completed this month'
        }
      },
      layout: { x: 9, y: 0, w: 3, h: 3 }
    },
    {
      id: 'completion-trends',
      type: 'chart' as const,
      title: 'Training Completion Trends',
      component: ChartWidget,
      props: {
        type: 'line',
        height: 300
      },
      layout: { x: 0, y: 3, w: 8, h: 5 }
    },
    {
      id: 'training-by-type',
      type: 'chart' as const,
      title: 'Training by Type',
      component: ChartWidget,
      props: {
        type: 'doughnut',
        height: 300
      },
      layout: { x: 8, y: 3, w: 4, h: 5 }
    },
    {
      id: 'dept-compliance',
      type: 'chart' as const,
      title: 'Department Compliance Rates',
      component: ChartWidget,
      props: {
        type: 'bar',
        height: 250
      },
      layout: { x: 0, y: 8, w: 6, h: 4 }
    },
    {
      id: 'competency-matrix',
      type: 'chart' as const,
      title: 'Competency Achievement',
      component: ChartWidget,
      props: {
        type: 'bar',
        height: 250
      },
      layout: { x: 6, y: 8, w: 6, h: 4 }
    }
  ];

  const handleWidgetUpdate = (widgetId: string, data: any) => {
    console.log(`Training widget ${widgetId} updated:`, data);
    // Handle training dashboard specific updates
  };

  return (
    <DashboardLayout
      title="Training Management Dashboard"
      widgets={widgets}
      isEditable={true}
      autoRefresh={true}
      refreshInterval={120000} // 2 minutes for training data
      onWidgetUpdate={handleWidgetUpdate}
    />
  );
};

export default TrainingDashboard;