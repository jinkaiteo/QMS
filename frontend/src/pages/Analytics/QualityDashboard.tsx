// Quality Dashboard - Phase B Sprint 1 Day 3
// Quality-focused dashboard for quality managers and teams

import React from 'react';
import DashboardLayout from '../../components/Analytics/Dashboard/DashboardLayout';
import KPIWidget from '../../components/Analytics/Widgets/KPIWidget';
import ChartWidget from '../../components/Analytics/Widgets/ChartWidget';

const QualityDashboard: React.FC = () => {
  // Quality-focused dashboard configuration
  const widgets = [
    {
      id: 'quality-events-count',
      type: 'kpi' as const,
      title: 'Quality Events (Current Month)',
      component: KPIWidget,
      props: {
        data: {
          value: 15,
          unit: 'events',
          previousValue: 18,
          target: 12,
          trend: 'down' as const,
          trendPercentage: 16.7,
          status: 'good' as const,
          description: 'Total quality events reported this month'
        }
      },
      layout: { x: 0, y: 0, w: 3, h: 3 }
    },
    {
      id: 'capa-effectiveness',
      type: 'kpi' as const,
      title: 'CAPA Effectiveness Rate',
      component: KPIWidget,
      props: {
        data: {
          value: 87.5,
          unit: '%',
          previousValue: 82.1,
          target: 90,
          trend: 'up' as const,
          trendPercentage: 6.6,
          status: 'good' as const,
          description: 'Percentage of effective corrective actions'
        }
      },
      layout: { x: 3, y: 0, w: 3, h: 3 }
    },
    {
      id: 'resolution-time',
      type: 'kpi' as const,
      title: 'Average Resolution Time',
      component: KPIWidget,
      props: {
        data: {
          value: 5.5,
          unit: 'days',
          previousValue: 7.2,
          target: 5.0,
          trend: 'down' as const,
          trendPercentage: 23.6,
          status: 'warning' as const,
          description: 'Average time to resolve quality events'
        }
      },
      layout: { x: 6, y: 0, w: 3, h: 3 }
    },
    {
      id: 'compliance-score',
      type: 'kpi' as const,
      title: 'Compliance Score',
      component: KPIWidget,
      props: {
        data: {
          value: 94.2,
          unit: '%',
          previousValue: 91.8,
          target: 95,
          trend: 'up' as const,
          trendPercentage: 2.6,
          status: 'excellent' as const,
          description: 'Overall regulatory compliance score'
        }
      },
      layout: { x: 9, y: 0, w: 3, h: 3 }
    },
    {
      id: 'quality-events-trend',
      type: 'chart' as const,
      title: 'Quality Events Trend (6 Months)',
      component: ChartWidget,
      props: {
        type: 'line',
        height: 300
      },
      layout: { x: 0, y: 3, w: 8, h: 5 }
    },
    {
      id: 'events-by-severity',
      type: 'chart' as const,
      title: 'Events by Severity',
      component: ChartWidget,
      props: {
        type: 'pie',
        height: 300
      },
      layout: { x: 8, y: 3, w: 4, h: 5 }
    },
    {
      id: 'capa-status',
      type: 'chart' as const,
      title: 'CAPA Status Distribution',
      component: ChartWidget,
      props: {
        type: 'doughnut',
        height: 250
      },
      layout: { x: 0, y: 8, w: 4, h: 4 }
    },
    {
      id: 'department-quality',
      type: 'chart' as const,
      title: 'Quality Score by Department',
      component: ChartWidget,
      props: {
        type: 'bar',
        height: 250
      },
      layout: { x: 4, y: 8, w: 8, h: 4 }
    }
  ];

  const handleWidgetUpdate = (widgetId: string, data: any) => {
    console.log(`Quality widget ${widgetId} updated:`, data);
    // Handle quality dashboard specific updates
  };

  return (
    <DashboardLayout
      title="Quality Management Dashboard"
      widgets={widgets}
      isEditable={true}
      autoRefresh={true}
      refreshInterval={30000} // 30 seconds for quality monitoring
      onWidgetUpdate={handleWidgetUpdate}
    />
  );
};

export default QualityDashboard;