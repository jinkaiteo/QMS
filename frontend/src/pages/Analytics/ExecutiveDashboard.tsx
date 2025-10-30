// Executive Dashboard - Phase B Sprint 1 Day 3
// High-level overview dashboard for executives and managers

import React from 'react';
import DashboardLayout from '../../components/Analytics/Dashboard/DashboardLayout';
import KPIWidget from '../../components/Analytics/Widgets/KPIWidget';
import ChartWidget from '../../components/Analytics/Widgets/ChartWidget';

const ExecutiveDashboard: React.FC = () => {
  // Dashboard configuration with widgets
  const widgets = [
    {
      id: 'quality-score',
      type: 'kpi' as const,
      title: 'Overall Quality Score',
      component: KPIWidget,
      props: {
        data: {
          value: 92,
          unit: '%',
          previousValue: 88,
          target: 95,
          trend: 'up' as const,
          trendPercentage: 4.5,
          status: 'good' as const,
          description: 'Composite quality score across all departments'
        }
      },
      layout: { x: 0, y: 0, w: 3, h: 3 }
    },
    {
      id: 'training-compliance',
      type: 'kpi' as const,
      title: 'Training Compliance',
      component: KPIWidget,
      props: {
        data: {
          value: 87,
          unit: '%',
          previousValue: 85,
          target: 90,
          trend: 'up' as const,
          trendPercentage: 2.4,
          status: 'warning' as const,
          description: 'Percentage of employees with up-to-date training'
        }
      },
      layout: { x: 3, y: 0, w: 3, h: 3 }
    },
    {
      id: 'document-efficiency',
      type: 'kpi' as const,
      title: 'Document Efficiency',
      component: KPIWidget,
      props: {
        data: {
          value: 3.2,
          unit: 'days',
          previousValue: 4.1,
          target: 3.0,
          trend: 'down' as const,
          trendPercentage: 22.0,
          status: 'good' as const,
          description: 'Average document approval time'
        }
      },
      layout: { x: 6, y: 0, w: 3, h: 3 }
    },
    {
      id: 'active-capas',
      type: 'kpi' as const,
      title: 'Active CAPAs',
      component: KPIWidget,
      props: {
        data: {
          value: 12,
          unit: 'open',
          previousValue: 15,
          target: 8,
          trend: 'down' as const,
          trendPercentage: 20.0,
          status: 'warning' as const,
          description: 'Number of open corrective and preventive actions'
        }
      },
      layout: { x: 9, y: 0, w: 3, h: 3 }
    },
    {
      id: 'quality-trends',
      type: 'chart' as const,
      title: 'Quality Metrics Trends',
      component: ChartWidget,
      props: {
        type: 'line',
        height: 250
      },
      layout: { x: 0, y: 3, w: 6, h: 4 }
    },
    {
      id: 'department-performance',
      type: 'chart' as const,
      title: 'Department Performance',
      component: ChartWidget,
      props: {
        type: 'bar',
        height: 250
      },
      layout: { x: 6, y: 3, w: 6, h: 4 }
    },
    {
      id: 'compliance-breakdown',
      type: 'chart' as const,
      title: 'Compliance Status Breakdown',
      component: ChartWidget,
      props: {
        type: 'doughnut',
        height: 200
      },
      layout: { x: 0, y: 7, w: 4, h: 3 }
    },
    {
      id: 'training-progress',
      type: 'chart' as const,
      title: 'Training Progress by Department',
      component: ChartWidget,
      props: {
        type: 'bar',
        height: 200
      },
      layout: { x: 4, y: 7, w: 4, h: 3 }
    },
    {
      id: 'recent-events',
      type: 'kpi' as const,
      title: 'Quality Events (30 days)',
      component: KPIWidget,
      props: {
        data: {
          value: 8,
          unit: 'events',
          previousValue: 12,
          target: 5,
          trend: 'down' as const,
          trendPercentage: 33.3,
          status: 'good' as const,
          description: 'Total quality events in the last 30 days'
        }
      },
      layout: { x: 8, y: 7, w: 4, h: 3 }
    }
  ];

  const handleWidgetUpdate = (widgetId: string, data: any) => {
    console.log(`Widget ${widgetId} updated:`, data);
    // Handle real-time widget updates here
  };

  const handleLayoutChange = (layout: any[]) => {
    console.log('Dashboard layout changed:', layout);
    // Save layout changes to user preferences
  };

  return (
    <DashboardLayout
      title="Executive Dashboard"
      widgets={widgets}
      isEditable={false}
      autoRefresh={true}
      refreshInterval={60000} // 1 minute
      onWidgetUpdate={handleWidgetUpdate}
      onLayoutChange={handleLayoutChange}
    />
  );
};

export default ExecutiveDashboard;