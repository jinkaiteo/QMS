// Notification Management Dashboard - Phase C Frontend Development Continuation
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  IconButton
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
  Schedule as ScheduleIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  Send as SendIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import {
  notificationService,
  NotificationTemplate,
  NotificationRequest,
  NotificationStatus,
  DeliveryMetrics,
  NotificationPreferences,
  ScheduledNotification
} from '../../services/notificationService';

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
      id={`notification-tabpanel-${index}`}
      aria-labelledby={`notification-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const NotificationDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for notification data
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  const [metrics, setMetrics] = useState<DeliveryMetrics | null>(null);
  const [scheduledNotifications, setScheduledNotifications] = useState<ScheduledNotification[]>([]);
  const [userPreferences, setUserPreferences] = useState<NotificationPreferences | null>(null);

  // Dialog state
  const [showSendDialog, setShowSendDialog] = useState(false);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [showPreferencesDialog, setShowPreferencesDialog] = useState(false);

  // Form state
  const [notificationRequest, setNotificationRequest] = useState<Partial<NotificationRequest>>({
    priority: 'normal'
  });
  const [newTemplate, setNewTemplate] = useState<Partial<NotificationTemplate>>({
    template_type: 'system',
    is_active: true,
    variables: []
  });

  useEffect(() => {
    loadNotificationData();
  }, []);

  const loadNotificationData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all notification data
      const [templatesData, metricsData, scheduledData, preferencesData] = await Promise.all([
        notificationService.getNotificationTemplates(),
        notificationService.getNotificationMetrics(
          new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          new Date().toISOString()
        ),
        notificationService.getScheduledNotifications(),
        notificationService.getNotificationPreferences(1) // Current user
      ]);

      setTemplates(templatesData);
      setMetrics(metricsData);
      setScheduledNotifications(scheduledData.scheduled_notifications);
      setUserPreferences(preferencesData);

    } catch (err) {
      setError('Failed to load notification data. Please try again.');
      console.error('Notification data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleSendNotification = async () => {
    if (!notificationRequest.template_id || !notificationRequest.recipients?.length) {
      setError('Please select a template and add recipients');
      return;
    }

    try {
      setLoading(true);
      const result = await notificationService.sendNotification(notificationRequest as NotificationRequest);
      if (result.success) {
        setShowSendDialog(false);
        setNotificationRequest({ priority: 'normal' });
        await loadNotificationData();
      }
    } catch (err) {
      setError('Failed to send notification. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = async () => {
    if (!newTemplate.name || !newTemplate.subject_template || !newTemplate.body_template) {
      setError('Please fill in all required template fields');
      return;
    }

    try {
      setLoading(true);
      const result = await notificationService.createNotificationTemplate(
        newTemplate as Omit<NotificationTemplate, 'template_id' | 'created_at'>
      );
      if (result.success) {
        setShowTemplateDialog(false);
        setNewTemplate({
          template_type: 'system',
          is_active: true,
          variables: []
        });
        await loadNotificationData();
      }
    } catch (err) {
      setError('Failed to create template. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getDeliveryStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'delivered': return '#4caf50';
      case 'sent': return '#2196f3';
      case 'failed': return '#f44336';
      case 'pending': return '#ff9800';
      default: return '#9e9e9e';
    }
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

  // Sample data for charts
  const deliveryTrendData = [
    { date: '2024-12-12', sent: 145, delivered: 138, failed: 7 },
    { date: '2024-12-13', sent: 167, delivered: 159, failed: 8 },
    { date: '2024-12-14', sent: 123, delivered: 118, failed: 5 },
    { date: '2024-12-15', sent: 189, delivered: 182, failed: 7 },
    { date: '2024-12-16', sent: 203, delivered: 195, failed: 8 },
    { date: '2024-12-17', sent: 178, delivered: 169, failed: 9 },
    { date: '2024-12-18', sent: 156, delivered: 148, failed: 8 }
  ];

  const channelDistributionData = [
    { name: 'Email', value: 75, color: '#2196f3' },
    { name: 'SMS', value: 15, color: '#4caf50' },
    { name: 'Push', value: 10, color: '#ff9800' }
  ];

  if (loading && !templates.length) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} />
        <Typography sx={{ ml: 2 }}>Loading Notification Dashboard...</Typography>
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ width: '100%' }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Notification Management Dashboard
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Multi-Channel Communication & Delivery Analytics
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={() => setShowSendDialog(true)}
            >
              Send Notification
            </Button>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => setShowTemplateDialog(true)}
            >
              New Template
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadNotificationData}
              disabled={loading}
            >
              Refresh
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
            <Tab label="Overview" icon={<NotificationsIcon />} />
            <Tab label="Templates" icon={<EmailIcon />} />
            <Tab label="Scheduled" icon={<ScheduleIcon />} />
            <Tab label="Analytics" icon={<AssessmentIcon />} />
            <Tab label="Preferences" icon={<SettingsIcon />} />
          </Tabs>
        </Paper>

        {/* Overview Tab */}
        <TabPanel value={activeTab} index={0}>
          {metrics && (
            <Grid container spacing={3}>
              {/* Key Metrics Cards */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Total Sent
                    </Typography>
                    <Typography variant="h4" component="div">
                      {metrics.total_sent.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="primary.main">
                      Last 30 days
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Delivery Rate
                    </Typography>
                    <Typography variant="h4" component="div" color="success.main">
                      {Math.round(metrics.delivery_rate)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {metrics.total_delivered} delivered
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Open Rate
                    </Typography>
                    <Typography variant="h4" component="div" color="info.main">
                      {Math.round(metrics.open_rate)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {metrics.total_opened} opened
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Failed Rate
                    </Typography>
                    <Typography variant="h4" component="div" color="error.main">
                      {Math.round(metrics.bounce_rate)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {metrics.total_failed} failed
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Delivery Trend Chart */}
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Delivery Trends (Last 7 Days)
                    </Typography>
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={deliveryTrendData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Area type="monotone" dataKey="sent" stackId="1" stroke="#2196f3" fill="#2196f3" />
                          <Area type="monotone" dataKey="delivered" stackId="2" stroke="#4caf50" fill="#4caf50" />
                          <Area type="monotone" dataKey="failed" stackId="3" stroke="#f44336" fill="#f44336" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Channel Distribution */}
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Channel Distribution
                    </Typography>
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={channelDistributionData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, value }) => `${name}: ${value}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {channelDistributionData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* Templates Tab */}
        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Notification Templates ({templates.length})
              </Typography>
            </Grid>
            {templates.map((template) => (
              <Grid item xs={12} md={6} lg={4} key={template.template_id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="h6">
                        {template.name}
                      </Typography>
                      <Box>
                        <Chip 
                          label={template.template_type} 
                          size="small" 
                          color="primary"
                          sx={{ mr: 1 }}
                        />
                        <Chip 
                          label={template.is_active ? 'Active' : 'Inactive'} 
                          size="small" 
                          color={template.is_active ? 'success' : 'default'}
                        />
                      </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {template.description}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Subject:</strong> {template.subject_template}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Variables:</strong> {template.variables.join(', ') || 'None'}
                    </Typography>
                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        startIcon={<SendIcon />}
                        onClick={() => {
                          setNotificationRequest(prev => ({ ...prev, template_id: template.template_id }));
                          setShowSendDialog(true);
                        }}
                      >
                        Use Template
                      </Button>
                      <IconButton size="small">
                        <EditIcon />
                      </IconButton>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* Scheduled Tab */}
        <TabPanel value={activeTab} index={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Scheduled Notifications ({scheduledNotifications.length})
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Template</TableCell>
                      <TableCell>Recipients</TableCell>
                      <TableCell>Scheduled Time</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {scheduledNotifications.map((scheduled) => (
                      <TableRow key={scheduled.schedule_id}>
                        <TableCell>{scheduled.template_id}</TableCell>
                        <TableCell>{scheduled.recipients.length} recipients</TableCell>
                        <TableCell>{new Date(scheduled.scheduled_time).toLocaleString()}</TableCell>
                        <TableCell>
                          <Chip 
                            label={scheduled.status} 
                            size="small"
                            color={scheduled.status === 'pending' ? 'warning' : 
                                  scheduled.status === 'sent' ? 'success' : 'default'}
                          />
                        </TableCell>
                        <TableCell>
                          {scheduled.status === 'pending' && (
                            <IconButton 
                              size="small" 
                              color="error"
                              onClick={() => notificationService.cancelScheduledNotification(scheduled.schedule_id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Analytics Tab */}
        <TabPanel value={activeTab} index={3}>
          {metrics && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Performance Metrics
                    </Typography>
                    <List>
                      <ListItem>
                        <ListItemText 
                          primary="Delivery Rate" 
                          secondary={`${Math.round(metrics.delivery_rate)}% (${metrics.total_delivered}/${metrics.total_sent})`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Open Rate" 
                          secondary={`${Math.round(metrics.open_rate)}% (${metrics.total_opened} opened)`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Click Rate" 
                          secondary={`${Math.round(metrics.click_rate)}% (${metrics.total_clicked} clicked)`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Bounce Rate" 
                          secondary={`${Math.round(metrics.bounce_rate)}% (${metrics.total_failed} failed)`}
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Channel Performance
                    </Typography>
                    <Box sx={{ height: 200 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={channelDistributionData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="value" fill="#2196f3" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* Preferences Tab */}
        <TabPanel value={activeTab} index={4}>
          {userPreferences && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Notification Preferences
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Delivery Channels
                    </Typography>
                    <FormControlLabel
                      control={<Switch checked={userPreferences.email_enabled} />}
                      label="Email Notifications"
                    />
                    <FormControlLabel
                      control={<Switch checked={userPreferences.sms_enabled} />}
                      label="SMS Notifications"
                    />
                    <FormControlLabel
                      control={<Switch checked={userPreferences.push_enabled} />}
                      label="Push Notifications"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Frequency Settings
                    </Typography>
                    <FormControl fullWidth sx={{ mb: 2 }}>
                      <InputLabel>Notification Frequency</InputLabel>
                      <Select value={userPreferences.frequency} label="Notification Frequency">
                        <MenuItem value="immediate">Immediate</MenuItem>
                        <MenuItem value="hourly">Hourly Digest</MenuItem>
                        <MenuItem value="daily">Daily Digest</MenuItem>
                        <MenuItem value="weekly">Weekly Digest</MenuItem>
                      </Select>
                    </FormControl>
                    <TextField
                      fullWidth
                      label="Quiet Hours Start"
                      value={userPreferences.quiet_hours_start || ''}
                      sx={{ mb: 1 }}
                    />
                    <TextField
                      fullWidth
                      label="Quiet Hours End"
                      value={userPreferences.quiet_hours_end || ''}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}
        </TabPanel>

        {/* Send Notification Dialog */}
        <Dialog open={showSendDialog} onClose={() => setShowSendDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Send Notification</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Template</InputLabel>
                  <Select
                    value={notificationRequest.template_id || ''}
                    label="Template"
                    onChange={(e) => setNotificationRequest(prev => ({ ...prev, template_id: e.target.value }))}
                  >
                    {templates.map((template) => (
                      <MenuItem key={template.template_id} value={template.template_id}>
                        {template.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Recipients (comma-separated emails)"
                  multiline
                  rows={3}
                  value={notificationRequest.recipients?.join(', ') || ''}
                  onChange={(e) => setNotificationRequest(prev => ({ 
                    ...prev, 
                    recipients: e.target.value.split(',').map(r => r.trim()) 
                  }))}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={notificationRequest.priority || 'normal'}
                    label="Priority"
                    onChange={(e) => setNotificationRequest(prev => ({ ...prev, priority: e.target.value as any }))}
                  >
                    <MenuItem value="critical">Critical</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="normal">Normal</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowSendDialog(false)}>Cancel</Button>
            <Button onClick={handleSendNotification} variant="contained" disabled={loading}>
              {loading ? <CircularProgress size={24} /> : 'Send Notification'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Create Template Dialog */}
        <Dialog open={showTemplateDialog} onClose={() => setShowTemplateDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Create New Template</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Template Name"
                  value={newTemplate.name || ''}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, name: e.target.value }))}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Template Type</InputLabel>
                  <Select
                    value={newTemplate.template_type || 'system'}
                    label="Template Type"
                    onChange={(e) => setNewTemplate(prev => ({ ...prev, template_type: e.target.value }))}
                  >
                    <MenuItem value="system">System</MenuItem>
                    <MenuItem value="alert">Alert</MenuItem>
                    <MenuItem value="reminder">Reminder</MenuItem>
                    <MenuItem value="marketing">Marketing</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  multiline
                  rows={2}
                  value={newTemplate.description || ''}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, description: e.target.value }))}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Subject Template"
                  value={newTemplate.subject_template || ''}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, subject_template: e.target.value }))}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Body Template"
                  multiline
                  rows={6}
                  value={newTemplate.body_template || ''}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, body_template: e.target.value }))}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Variables (comma-separated)"
                  placeholder="user_name, report_name, due_date"
                  value={newTemplate.variables?.join(', ') || ''}
                  onChange={(e) => setNewTemplate(prev => ({ 
                    ...prev, 
                    variables: e.target.value.split(',').map(v => v.trim()).filter(v => v)
                  }))}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowTemplateDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateTemplate} variant="contained" disabled={loading}>
              {loading ? <CircularProgress size={24} /> : 'Create Template'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
};

export default NotificationDashboard;