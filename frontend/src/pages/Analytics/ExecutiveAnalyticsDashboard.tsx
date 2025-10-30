// Executive Analytics Dashboard - Phase C Frontend Development
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tab,
  Tabs,
  Paper
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Speed as SpeedIcon,
  Psychology as PsychologyIcon,
  Assessment as AssessmentIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar
} from 'recharts';
import { 
  advancedAnalyticsService,
  DashboardMetrics,
  ModuleHealth,
  AnalyticsInsight,
  TrendAnalysis,
  ComplianceStatus,
  SystemPerformance,
  PredictiveInsights
} from '../../services/advancedAnalyticsService';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`dashboard-tabpanel-${index}`}
      aria-labelledby={`dashboard-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ExecutiveAnalyticsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [timeRange, setTimeRange] = useState('30d');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // State for dashboard data
  const [dashboardMetrics, setDashboardMetrics] = useState<DashboardMetrics | null>(null);
  const [moduleHealth, setModuleHealth] = useState<ModuleHealth[]>([]);
  const [insights, setInsights] = useState<AnalyticsInsight[]>([]);
  const [trends, setTrends] = useState<TrendAnalysis[]>([]);
  const [complianceStatus, setComplianceStatus] = useState<ComplianceStatus | null>(null);
  const [systemPerformance, setSystemPerformance] = useState<SystemPerformance | null>(null);
  const [predictiveInsights, setPredictiveInsights] = useState<PredictiveInsights | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, [timeRange]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all dashboard data concurrently
      const [
        metricsData,
        healthData,
        insightsData,
        trendsData,
        complianceData,
        performanceData,
        predictiveData
      ] = await Promise.all([
        advancedAnalyticsService.getDashboardOverview(parseInt(timeRange.replace('d', ''))),
        advancedAnalyticsService.getModuleHealth(),
        advancedAnalyticsService.getAnalyticsInsights(),
        advancedAnalyticsService.getTrendAnalysis(['user_activity', 'compliance_score', 'system_utilization'], timeRange),
        advancedAnalyticsService.getComplianceStatus(),
        advancedAnalyticsService.getSystemPerformance(),
        advancedAnalyticsService.getPredictiveInsights()
      ]);

      setDashboardMetrics(metricsData);
      setModuleHealth(healthData);
      setInsights(insightsData);
      setTrends(trendsData);
      setComplianceStatus(complianceData);
      setSystemPerformance(performanceData);
      setPredictiveInsights(predictiveData);

    } catch (err) {
      setError('Failed to load dashboard data. Please try again.');
      console.error('Dashboard loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status.toLowerCase()) {
      case 'operational':
      case 'healthy':
      case 'compliant':
        return 'success';
      case 'warning':
      case 'degraded':
        return 'warning';
      case 'error':
      case 'critical':
      case 'non_compliant':
        return 'error';
      default:
        return 'default';
    }
  };

  const getImpactColor = (level: string): string => {
    switch (level.toLowerCase()) {
      case 'critical':
        return '#f44336';
      case 'high':
        return '#ff9800';
      case 'medium':
        return '#2196f3';
      case 'low':
        return '#4caf50';
      default:
        return '#9e9e9e';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} />
        <Typography sx={{ ml: 2 }}>Loading Executive Dashboard...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={loadDashboardData}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Executive Analytics Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            AI-Powered Insights and Real-Time Analytics
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
              <MenuItem value="365d">Last year</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadDashboardData}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Tab Navigation */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} variant="fullWidth">
          <Tab label="Overview" icon={<DashboardIcon />} />
          <Tab label="System Health" icon={<SpeedIcon />} />
          <Tab label="AI Insights" icon={<PsychologyIcon />} />
          <Tab label="Trends" icon={<TrendingUpIcon />} />
          <Tab label="Compliance" icon={<CheckCircleIcon />} />
          <Tab label="Predictive" icon={<AssessmentIcon />} />
        </Tabs>
      </Paper>

      {/* Overview Tab */}
      <TabPanel value={activeTab} index={0}>
        {dashboardMetrics && (
          <Grid container spacing={3}>
            {/* Key Metrics Cards */}
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Total Users
                  </Typography>
                  <Typography variant="h4" component="div">
                    {dashboardMetrics.total_users.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active system users
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Active Documents
                  </Typography>
                  <Typography variant="h4" component="div">
                    {dashboardMetrics.active_documents.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Documents in system
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Pending Trainings
                  </Typography>
                  <Typography variant="h4" component="div" color="warning.main">
                    {dashboardMetrics.pending_trainings}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Require attention
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Quality Events
                  </Typography>
                  <Typography variant="h4" component="div" color="error.main">
                    {dashboardMetrics.open_quality_events}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Open events
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* System Utilization */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Utilization
                  </Typography>
                  <Box sx={{ position: 'relative', display: 'inline-flex', width: '100%', justifyContent: 'center' }}>
                    <CircularProgress
                      variant="determinate"
                      value={dashboardMetrics.system_utilization * 100}
                      size={120}
                      thickness={4}
                      color={dashboardMetrics.system_utilization > 0.8 ? 'error' : dashboardMetrics.system_utilization > 0.6 ? 'warning' : 'success'}
                    />
                    <Box
                      sx={{
                        top: 0,
                        left: 0,
                        bottom: 0,
                        right: 0,
                        position: 'absolute',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Typography variant="h4" component="div">
                        {Math.round(dashboardMetrics.system_utilization * 100)}%
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Compliance Score */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Compliance Score
                  </Typography>
                  <Box sx={{ position: 'relative', display: 'inline-flex', width: '100%', justifyContent: 'center' }}>
                    <CircularProgress
                      variant="determinate"
                      value={dashboardMetrics.compliance_score * 100}
                      size={120}
                      thickness={4}
                      color={dashboardMetrics.compliance_score > 0.9 ? 'success' : dashboardMetrics.compliance_score > 0.7 ? 'warning' : 'error'}
                    />
                    <Box
                      sx={{
                        top: 0,
                        left: 0,
                        bottom: 0,
                        right: 0,
                        position: 'absolute',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Typography variant="h4" component="div">
                        {Math.round(dashboardMetrics.compliance_score * 100)}%
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </TabPanel>

      {/* System Health Tab */}
      <TabPanel value={activeTab} index={1}>
        <Grid container spacing={3}>
          {/* Module Health Cards */}
          {moduleHealth.map((module) => (
            <Grid item xs={12} md={6} lg={4} key={module.module_name}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      {module.module_name}
                    </Typography>
                    <Chip 
                      label={module.status} 
                      color={getStatusColor(module.status)}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Active Users: {module.active_users}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Error Rate: {(module.error_rate * 100).toFixed(2)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Performance: {Math.round(module.performance_score * 100)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}

          {/* System Performance Chart */}
          {systemPerformance && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Performance Metrics
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" gutterBottom>CPU Usage</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ width: '100%', mr: 1 }}>
                          <CircularProgress
                            variant="determinate"
                            value={systemPerformance.cpu_usage}
                            size={40}
                            color={systemPerformance.cpu_usage > 80 ? 'error' : systemPerformance.cpu_usage > 60 ? 'warning' : 'success'}
                          />
                        </Box>
                        <Typography variant="body2">{systemPerformance.cpu_usage.toFixed(1)}%</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" gutterBottom>Memory Usage</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ width: '100%', mr: 1 }}>
                          <CircularProgress
                            variant="determinate"
                            value={systemPerformance.memory_usage}
                            size={40}
                            color={systemPerformance.memory_usage > 80 ? 'error' : systemPerformance.memory_usage > 60 ? 'warning' : 'success'}
                          />
                        </Box>
                        <Typography variant="body2">{systemPerformance.memory_usage.toFixed(1)}%</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" gutterBottom>API Response Time</Typography>
                      <Typography variant="h6">{systemPerformance.api_response_time.toFixed(0)}ms</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" gutterBottom>Uptime</Typography>
                      <Typography variant="h6" color="success.main">{systemPerformance.uptime_percentage.toFixed(2)}%</Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </TabPanel>

      {/* AI Insights Tab */}
      <TabPanel value={activeTab} index={2}>
        <Grid container spacing={3}>
          {insights.map((insight, index) => (
            <Grid item xs={12} md={6} key={insight.insight_id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" sx={{ flexGrow: 1 }}>
                      {insight.title}
                    </Typography>
                    <Chip 
                      label={insight.impact_level}
                      sx={{ backgroundColor: getImpactColor(insight.impact_level), color: 'white' }}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" paragraph>
                    {insight.description}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                    {insight.action_required && (
                      <Chip 
                        icon={<WarningIcon />}
                        label="Action Required" 
                        color="warning" 
                        size="small"
                        sx={{ mr: 1 }}
                      />
                    )}
                    <Chip label={insight.category} variant="outlined" size="small" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* Trends Tab */}
      <TabPanel value={activeTab} index={3}>
        <Grid container spacing={3}>
          {trends.map((trend, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {trend.metric_name} Trend
                  </Typography>
                  <Box sx={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={trend.data_points}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Line 
                          type="monotone" 
                          dataKey="value" 
                          stroke="#2196f3" 
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Trend: {trend.trend_direction} ({trend.percentage_change > 0 ? '+' : ''}{trend.percentage_change.toFixed(1)}%)
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Confidence: {Math.round(trend.confidence_level * 100)}%
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* Compliance Tab */}
      <TabPanel value={activeTab} index={4}>
        {complianceStatus && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Compliance Overview
                  </Typography>
                  <Typography variant="h3" color={complianceStatus.overall_score > 90 ? 'success.main' : complianceStatus.overall_score > 70 ? 'warning.main' : 'error.main'}>
                    {Math.round(complianceStatus.overall_score)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Overall Compliance Score
                  </Typography>
                  <Chip 
                    label={complianceStatus.audit_readiness} 
                    color={complianceStatus.audit_readiness === 'ready' ? 'success' : 'warning'}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Module Scores
                  </Typography>
                  {Object.entries(complianceStatus.module_scores).map(([module, score]) => (
                    <Box key={module} sx={{ mb: 1 }}>
                      <Typography variant="body2">{module}: {Math.round(score)}%</Typography>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Critical Issues & Recommendations
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>Critical Issues:</Typography>
                      {complianceStatus.critical_issues.map((issue, index) => (
                        <Alert key={index} severity="error" sx={{ mb: 1 }}>
                          {issue}
                        </Alert>
                      ))}
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>Recommendations:</Typography>
                      {complianceStatus.recommendations.map((rec, index) => (
                        <Alert key={index} severity="info" sx={{ mb: 1 }}>
                          {rec}
                        </Alert>
                      ))}
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </TabPanel>

      {/* Predictive Tab */}
      <TabPanel value={activeTab} index={5}>
        {predictiveInsights && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Capacity Forecast
                  </Typography>
                  <Typography variant="h4" color="primary">
                    {predictiveInsights.capacity_forecast.total_predicted_deliveries || 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Predicted deliveries (next 30 days)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Optimization Opportunities
                  </Typography>
                  {predictiveInsights.optimization_opportunities.slice(0, 3).map((opportunity, index) => (
                    <Typography key={index} variant="body2" paragraph>
                      • {opportunity}
                    </Typography>
                  ))}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Bottleneck Predictions
                  </Typography>
                  <Grid container spacing={2}>
                    {predictiveInsights.bottleneck_predictions.map((prediction, index) => (
                      <Grid item xs={12} md={6} key={index}>
                        <Alert severity="warning">
                          {prediction}
                        </Alert>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </TabPanel>
    </Box>
  );
};

export default ExecutiveAnalyticsDashboard;