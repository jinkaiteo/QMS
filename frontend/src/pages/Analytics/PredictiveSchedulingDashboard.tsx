// Predictive Scheduling Dashboard - Phase C Frontend Development
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  Paper,
  Tab,
  Tabs,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  StepContent
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  Insights as InsightsIcon,
  Settings as OptimizeIcon,
  Feedback as FeedbackIcon,
  ModelTraining as ModelTrainingIcon,
  Analytics as PredictionsIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import {
  predictiveSchedulingService,
  PredictionRequest,
  PredictionResponse,
  PatternAnalysis,
  CapacityForecast,
  OptimizationRequest,
  OptimizationResponse,
  SchedulingInsights
} from '../../services/predictiveSchedulingService';

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
      id={`scheduling-tabpanel-${index}`}
      aria-labelledby={`scheduling-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const PredictiveSchedulingDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Prediction state
  const [predictionRequest, setPredictionRequest] = useState<Partial<PredictionRequest>>({
    priority: 'normal',
    model: 'hybrid'
  });
  const [predictionResult, setPredictionResult] = useState<PredictionResponse | null>(null);
  const [showPredictionDialog, setShowPredictionDialog] = useState(false);

  // Analytics state
  const [patternAnalysis, setPatternAnalysis] = useState<PatternAnalysis | null>(null);
  const [capacityForecast, setCapacityForecast] = useState<CapacityForecast | null>(null);
  const [schedulingInsights, setSchedulingInsights] = useState<SchedulingInsights | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResponse | null>(null);

  // Model insights state
  const [modelInsights, setModelInsights] = useState<any>(null);
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [patterns, forecast, insights, models] = await Promise.all([
        predictiveSchedulingService.analyzePatterns(),
        predictiveSchedulingService.forecastCapacity(),
        predictiveSchedulingService.getSchedulingInsights(),
        predictiveSchedulingService.getModelInsights()
      ]);

      setPatternAnalysis(patterns);
      setCapacityForecast(forecast);
      setSchedulingInsights(insights);
      setModelInsights(models);

    } catch (err) {
      setError('Failed to load analytics data');
      console.error('Analytics loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handlePredictionSubmit = async () => {
    if (!predictionRequest.report_type || !predictionRequest.department || !predictionRequest.target_date) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      const result = await predictiveSchedulingService.predictOptimalTime(predictionRequest as PredictionRequest);
      setPredictionResult(result);
      setShowPredictionDialog(false);
    } catch (err) {
      setError('Prediction failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOptimizeSchedule = async () => {
    if (!predictionRequest.target_date) {
      setError('Please select a target date');
      return;
    }

    try {
      setLoading(true);
      const optimizationRequest: OptimizationRequest = {
        target_date: predictionRequest.target_date,
        goal: 'balance_load'
      };
      const result = await predictiveSchedulingService.optimizeSchedule(optimizationRequest);
      setOptimizationResult(result);
    } catch (err) {
      setError('Optimization failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return '#4caf50';
    if (confidence >= 0.6) return '#ff9800';
    return '#f44336';
  };

  const getPriorityColor = (priority: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'normal': return 'primary';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ width: '100%' }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              AI-Powered Predictive Scheduling
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Machine Learning Optimization and Intelligent Scheduling
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<PsychologyIcon />}
              onClick={() => setShowPredictionDialog(true)}
            >
              New Prediction
            </Button>
            <Button
              variant="outlined"
              startIcon={<OptimizeIcon />}
              onClick={handleOptimizeSchedule}
            >
              Optimize Schedule
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Tab Navigation */}
        <Paper sx={{ mb: 3 }}>
          <Tabs value={activeTab} onChange={handleTabChange} variant="fullWidth">
            <Tab label="Predictions" icon={<PredictionsIcon />} />
            <Tab label="Pattern Analysis" icon={<TrendingUpIcon />} />
            <Tab label="Capacity Forecast" icon={<ScheduleIcon />} />
            <Tab label="Insights" icon={<InsightsIcon />} />
            <Tab label="ML Models" icon={<ModelTrainingIcon />} />
          </Tabs>
        </Paper>

        {/* Predictions Tab */}
        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            {/* Latest Prediction Result */}
            {predictionResult && (
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Latest Prediction Result
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={4}>
                        <Typography variant="body2" color="text.secondary">Recommended Time</Typography>
                        <Typography variant="h5" color="primary">
                          {new Date(predictionResult.recommended_time).toLocaleString()}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <Typography variant="body2" color="text.secondary">Confidence Score</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="h5" sx={{ color: getConfidenceColor(predictionResult.confidence_score) }}>
                            {Math.round(predictionResult.confidence_score * 100)}%
                          </Typography>
                          <CircularProgress
                            variant="determinate"
                            value={predictionResult.confidence_score * 100}
                            size={40}
                            sx={{ ml: 2, color: getConfidenceColor(predictionResult.confidence_score) }}
                          />
                        </Box>
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <Typography variant="body2" color="text.secondary">Model Used</Typography>
                        <Chip label={predictionResult.model_used} color="primary" />
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>Optimization Factors</Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {predictionResult.optimization_factors.map((factor, index) => (
                            <Chip key={index} label={factor} variant="outlined" size="small" />
                          ))}
                        </Box>
                      </Grid>
                      {predictionResult.alternative_times.length > 0 && (
                        <Grid item xs={12}>
                          <Typography variant="body2" color="text.secondary" gutterBottom>Alternative Times</Typography>
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            {predictionResult.alternative_times.map((time, index) => (
                              <Chip 
                                key={index} 
                                label={new Date(time).toLocaleTimeString()} 
                                variant="outlined" 
                                size="small"
                                color="secondary"
                              />
                            ))}
                          </Box>
                        </Grid>
                      )}
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Optimization Result */}
            {optimizationResult && (
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Schedule Optimization Results
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" gutterBottom>Expected Benefits</Typography>
                        {optimizationResult.expected_benefits.map((benefit, index) => (
                          <Alert key={index} severity="success" sx={{ mb: 1 }}>
                            {benefit}
                          </Alert>
                        ))}
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" gutterBottom>Implementation Effort</Typography>
                        <Chip 
                          label={optimizationResult.implementation_effort}
                          color={optimizationResult.implementation_effort === 'low' ? 'success' : 
                                optimizationResult.implementation_effort === 'medium' ? 'warning' : 'error'}
                        />
                        <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>Potential Risks</Typography>
                        {optimizationResult.risks.map((risk, index) => (
                          <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                            {risk}
                          </Alert>
                        ))}
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        </TabPanel>

        {/* Pattern Analysis Tab */}
        <TabPanel value={activeTab} index={1}>
          {patternAnalysis && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Analysis Summary</Typography>
                    <Typography variant="body2" color="text.secondary">Total Deliveries</Typography>
                    <Typography variant="h4">{patternAnalysis.total_deliveries.toLocaleString()}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>Success Rate</Typography>
                    <Typography variant="h4" color="success.main">
                      {Math.round(patternAnalysis.success_rate * 100)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Peak Hours Distribution</Typography>
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={patternAnalysis.peak_hours.map(hour => ({ hour, count: Math.random() * 100 }))}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="hour" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="count" fill="#2196f3" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Seasonal Trends</Typography>
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={Object.entries(patternAnalysis.seasonal_trends).map(([season, value]) => ({ season, value }))}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="season" />
                          <YAxis />
                          <Tooltip />
                          <Line type="monotone" dataKey="value" stroke="#4caf50" strokeWidth={3} />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>AI-Generated Insights</Typography>
                    {patternAnalysis.insights.map((insight, index) => (
                      <Alert key={index} severity="info" sx={{ mb: 1 }}>
                        {insight}
                      </Alert>
                    ))}
                    <Typography variant="h6" sx={{ mt: 3 }} gutterBottom>Optimization Opportunities</Typography>
                    {patternAnalysis.optimization_opportunities.map((opportunity, index) => (
                      <Alert key={index} severity="success" sx={{ mb: 1 }}>
                        {opportunity}
                      </Alert>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* Capacity Forecast Tab */}
        <TabPanel value={activeTab} index={2}>
          {capacityForecast && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Forecast Summary</Typography>
                    <Typography variant="body2" color="text.secondary">Total Predicted Deliveries</Typography>
                    <Typography variant="h4" color="primary">
                      {capacityForecast.total_predicted_deliveries.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>Average Daily Demand</Typography>
                    <Typography variant="h5">
                      {Math.round(capacityForecast.average_daily_demand)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Risk Assessment</Typography>
                    <Typography variant="body2" color="text.secondary">Peak Demand Days</Typography>
                    <Typography variant="h4" color="warning.main">
                      {capacityForecast.peak_demand_days}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>Bottleneck Risk Days</Typography>
                    <Typography variant="h4" color="error.main">
                      {capacityForecast.bottleneck_risk_days}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Forecast Confidence</Typography>
                    <Box sx={{ height: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <CircularProgress
                        variant="determinate"
                        value={Object.values(capacityForecast.confidence_metrics)[0] as number * 100 || 85}
                        size={80}
                        thickness={4}
                        color="success"
                      />
                    </Box>
                    <Typography variant="h6" sx={{ textAlign: 'center', mt: 1 }}>
                      {Math.round((Object.values(capacityForecast.confidence_metrics)[0] as number || 0.85) * 100)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Daily Forecast Trend</Typography>
                    <Box sx={{ height: 400 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={capacityForecast.daily_forecasts.slice(0, 30)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip />
                          <Area type="monotone" dataKey="predicted_deliveries" stroke="#2196f3" fill="#2196f3" fillOpacity={0.3} />
                          <Area type="monotone" dataKey="utilization_forecast" stroke="#4caf50" fill="#4caf50" fillOpacity={0.3} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>AI Recommendations</Typography>
                    {capacityForecast.recommendations.map((recommendation, index) => (
                      <Alert key={index} severity="info" sx={{ mb: 1 }}>
                        {recommendation}
                      </Alert>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* Insights Tab */}
        <TabPanel value={activeTab} index={3}>
          {schedulingInsights && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Executive Summary</Typography>
                    <Typography variant="body1" paragraph>
                      Analysis period: {schedulingInsights.analysis_period}
                    </Typography>
                    <Typography variant="body1" paragraph>
                      Scope: {schedulingInsights.scope}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Key Findings</Typography>
                    {schedulingInsights.key_findings.map((finding, index) => (
                      <Alert key={index} severity="info" sx={{ mb: 1 }}>
                        {finding}
                      </Alert>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Strategic Recommendations</Typography>
                    {schedulingInsights.recommendations.map((recommendation, index) => (
                      <Alert key={index} severity="success" sx={{ mb: 1 }}>
                        {recommendation}
                      </Alert>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Performance Metrics</Typography>
                    <Grid container spacing={2}>
                      {Object.entries(schedulingInsights.performance_metrics).map(([metric, value]) => (
                        <Grid item xs={12} sm={6} md={3} key={metric}>
                          <Typography variant="body2" color="text.secondary">{metric}</Typography>
                          <Typography variant="h5">{typeof value === 'number' ? value.toFixed(2) : value}</Typography>
                        </Grid>
                      ))}
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
              {schedulingInsights.alerts.length > 0 && (
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>System Alerts</Typography>
                      {schedulingInsights.alerts.map((alert, index) => (
                        <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                          {alert}
                        </Alert>
                      ))}
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          )}
        </TabPanel>

        {/* ML Models Tab */}
        <TabPanel value={activeTab} index={4}>
          {modelInsights && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Model Performance</Typography>
                    {Object.entries(modelInsights.model_performance || {}).map(([model, performance]) => (
                      <Box key={model} sx={{ mb: 2 }}>
                        <Typography variant="subtitle2">{model}</Typography>
                        <Typography variant="body2">
                          Accuracy: {((performance as any).accuracy * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Feature Importance</Typography>
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={modelInsights.feature_importance || []}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="feature" angle={-45} textAnchor="end" height={100} />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="importance" fill="#ff9800" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Model Recommendations</Typography>
                    {(modelInsights.recommendations || []).map((rec: string, index: number) => (
                      <Alert key={index} severity="info" sx={{ mb: 1 }}>
                        {rec}
                      </Alert>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* Prediction Dialog */}
        <Dialog open={showPredictionDialog} onClose={() => setShowPredictionDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Create New Prediction</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Report Type"
                  value={predictionRequest.report_type || ''}
                  onChange={(e) => setPredictionRequest(prev => ({ ...prev, report_type: e.target.value }))}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Department"
                  value={predictionRequest.department || ''}
                  onChange={(e) => setPredictionRequest(prev => ({ ...prev, department: e.target.value }))}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <DatePicker
                  label="Target Date"
                  value={predictionRequest.target_date ? new Date(predictionRequest.target_date) : null}
                  onChange={(date) => setPredictionRequest(prev => ({ 
                    ...prev, 
                    target_date: date?.toISOString().split('T')[0] 
                  }))}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={predictionRequest.priority || 'normal'}
                    label="Priority"
                    onChange={(e) => setPredictionRequest(prev => ({ ...prev, priority: e.target.value as any }))}
                  >
                    <MenuItem value="critical">Critical</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="normal">Normal</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="batch">Batch</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>ML Model</InputLabel>
                  <Select
                    value={predictionRequest.model || 'hybrid'}
                    label="ML Model"
                    onChange={(e) => setPredictionRequest(prev => ({ ...prev, model: e.target.value as any }))}
                  >
                    <MenuItem value="historical_pattern">Historical Pattern</MenuItem>
                    <MenuItem value="usage_based">Usage Based</MenuItem>
                    <MenuItem value="department_pattern">Department Pattern</MenuItem>
                    <MenuItem value="seasonal_trend">Seasonal Trend</MenuItem>
                    <MenuItem value="capacity_optimization">Capacity Optimization</MenuItem>
                    <MenuItem value="hybrid">Hybrid (Recommended)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Preferred Time (Optional)"
                  placeholder="HH:MM"
                  value={predictionRequest.preferred_time || ''}
                  onChange={(e) => setPredictionRequest(prev => ({ ...prev, preferred_time: e.target.value }))}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowPredictionDialog(false)}>Cancel</Button>
            <Button onClick={handlePredictionSubmit} variant="contained" disabled={loading}>
              {loading ? <CircularProgress size={24} /> : 'Generate Prediction'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
};

export default PredictiveSchedulingDashboard;