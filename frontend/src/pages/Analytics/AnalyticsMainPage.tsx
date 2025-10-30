// Analytics Main Page - Phase C Frontend Development
import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Paper,
  Stack
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Schedule as ScheduleIcon,
  Insights as InsightsIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface AnalyticsModule {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  path: string;
  features: string[];
  status: 'available' | 'beta' | 'coming_soon';
  color: string;
}

const AnalyticsMainPage: React.FC = () => {
  const navigate = useNavigate();

  const analyticsModules: AnalyticsModule[] = [
    {
      id: 'executive',
      title: 'Executive Analytics Dashboard',
      description: 'Comprehensive executive oversight with real-time metrics, AI-powered insights, and compliance monitoring across all QMS modules.',
      icon: <DashboardIcon sx={{ fontSize: 40 }} />,
      path: '/analytics/executive',
      features: [
        'Real-time KPI Monitoring',
        'AI-Generated Insights',
        'Module Health Status',
        'Compliance Scoring',
        'System Performance',
        'Predictive Analytics'
      ],
      status: 'available',
      color: '#1976d2'
    },
    {
      id: 'predictive-scheduling',
      title: 'AI-Powered Predictive Scheduling',
      description: 'Machine learning optimization for intelligent scheduling with 6 prediction models, pattern analysis, and capacity forecasting.',
      icon: <PsychologyIcon sx={{ fontSize: 40 }} />,
      path: '/analytics/predictive-scheduling',
      features: [
        '6 ML Prediction Models',
        'Pattern Analysis',
        'Capacity Forecasting',
        'Schedule Optimization',
        'Continuous Learning',
        'Risk Assessment'
      ],
      status: 'available',
      color: '#9c27b0'
    },
    {
      id: 'advanced',
      title: 'Advanced Analytics Suite',
      description: 'Deep dive analytics with trend analysis, forecasting, and advanced data visualization for comprehensive business intelligence.',
      icon: <TrendingUpIcon sx={{ fontSize: 40 }} />,
      path: '/analytics/advanced',
      features: [
        'Trend Analysis',
        'Advanced Forecasting',
        'Data Visualization',
        'Statistical Analysis',
        'Custom Reports',
        'Export Capabilities'
      ],
      status: 'available',
      color: '#2e7d32'
    },
    {
      id: 'compliance',
      title: 'Compliance Analytics',
      description: 'Automated compliance monitoring with CFR Part 11, ISO 13485, data integrity checks, and regulatory reporting.',
      icon: <SecurityIcon sx={{ fontSize: 40 }} />,
      path: '/compliance',
      features: [
        'CFR Part 11 Compliance',
        'ISO 13485 Monitoring',
        'Data Integrity Checks',
        'Audit Trail Analysis',
        'Regulatory Reporting',
        'Risk Assessment'
      ],
      status: 'available',
      color: '#ed6c02'
    },
    {
      id: 'notifications',
      title: 'Communication Analytics',
      description: 'Advanced notification system with delivery tracking, template management, and communication performance analytics.',
      icon: <NotificationsIcon sx={{ fontSize: 40 }} />,
      path: '/notifications',
      features: [
        'Delivery Analytics',
        'Template Performance',
        'User Engagement',
        'Multi-Channel Tracking',
        'Response Analysis',
        'Optimization Insights'
      ],
      status: 'available',
      color: '#d32f2f'
    },
    {
      id: 'performance',
      title: 'System Performance Analytics',
      description: 'Real-time system monitoring with performance metrics, capacity planning, and infrastructure optimization insights.',
      icon: <SpeedIcon sx={{ fontSize: 40 }} />,
      path: '/system/performance',
      features: [
        'Real-time Monitoring',
        'Performance Metrics',
        'Capacity Planning',
        'Resource Optimization',
        'Alert Management',
        'Trend Analysis'
      ],
      status: 'beta',
      color: '#0288d1'
    }
  ];

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'available':
        return <Chip label="Available" color="success" size="small" />;
      case 'beta':
        return <Chip label="Beta" color="warning" size="small" />;
      case 'coming_soon':
        return <Chip label="Coming Soon" color="default" size="small" />;
      default:
        return null;
    }
  };

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Advanced Analytics Suite
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          Comprehensive business intelligence powered by AI and machine learning
        </Typography>
        <Paper sx={{ p: 3, bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.200' }}>
          <Typography variant="body1" paragraph>
            <strong>🎉 New in Phase C:</strong> Our advanced analytics platform now includes AI-powered predictive scheduling, 
            executive intelligence dashboards, compliance automation, and comprehensive notification analytics.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Access real-time insights, predictive analytics, and automated compliance monitoring across all QMS modules.
          </Typography>
        </Paper>
      </Box>

      {/* Analytics Modules Grid */}
      <Grid container spacing={3}>
        {analyticsModules.map((module) => (
          <Grid item xs={12} lg={6} key={module.id}>
            <Card 
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ color: module.color, mr: 2 }}>
                    {module.icon}
                  </Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Typography variant="h5" component="h2">
                        {module.title}
                      </Typography>
                      {getStatusChip(module.status)}
                    </Box>
                    <Typography variant="body1" color="text.secondary" paragraph>
                      {module.description}
                    </Typography>
                  </Box>
                </Box>
                
                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                  Key Features:
                </Typography>
                <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                  {module.features.map((feature, index) => (
                    <Chip 
                      key={index}
                      label={feature}
                      variant="outlined"
                      size="small"
                      sx={{ 
                        borderColor: module.color,
                        color: module.color,
                        '&:hover': {
                          backgroundColor: `${module.color}10`
                        }
                      }}
                    />
                  ))}
                </Stack>
              </CardContent>
              
              <CardActions sx={{ p: 2, pt: 0 }}>
                <Button
                  variant="contained"
                  fullWidth
                  endIcon={<ArrowForwardIcon />}
                  onClick={() => handleNavigate(module.path)}
                  disabled={module.status === 'coming_soon'}
                  sx={{ 
                    backgroundColor: module.color,
                    '&:hover': {
                      backgroundColor: module.color,
                      filter: 'brightness(0.9)'
                    }
                  }}
                >
                  {module.status === 'coming_soon' ? 'Coming Soon' : 'Launch Analytics'}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Quick Stats Section */}
      <Box sx={{ mt: 6 }}>
        <Typography variant="h5" gutterBottom>
          Analytics Platform Overview
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Available Modules
                </Typography>
                <Typography variant="h4" component="div">
                  {analyticsModules.filter(m => m.status === 'available').length}
                </Typography>
                <Typography variant="body2" color="success.main">
                  Ready to use
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  AI/ML Models
                </Typography>
                <Typography variant="h4" component="div">
                  6+
                </Typography>
                <Typography variant="body2" color="primary.main">
                  Prediction models
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  API Endpoints
                </Typography>
                <Typography variant="h4" component="div">
                  56+
                </Typography>
                <Typography variant="body2" color="info.main">
                  Advanced APIs
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Real-time Data
                </Typography>
                <Typography variant="h4" component="div">
                  ✓
                </Typography>
                <Typography variant="body2" color="success.main">
                  Live analytics
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default AnalyticsMainPage;