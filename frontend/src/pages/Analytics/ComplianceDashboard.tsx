// Compliance Dashboard - Phase C Frontend Development Continuation
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
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Security as SecurityIcon,
  Assignment as AssignmentIcon,
  VerifiedUser as VerifiedUserIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  PlayArrow as PlayArrowIcon,
  ExpandMore as ExpandMoreIcon,
  Gavel as GavelIcon,
  Shield as ShieldIcon,
  Assessment as AssessmentIcon
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
  RadialBarChart,
  RadialBar
} from 'recharts';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import {
  complianceService,
  ComplianceAssessment,
  ValidationRule,
  CFRPart11Status,
  ISO13485Status,
  ComplianceDashboard as ComplianceDashboardData,
  AuditTrailEntry
} from '../../services/complianceService';

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
      id={`compliance-tabpanel-${index}`}
      aria-labelledby={`compliance-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ComplianceDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Dashboard state
  const [dashboardData, setDashboardData] = useState<ComplianceDashboardData | null>(null);
  const [complianceAssessment, setComplianceAssessment] = useState<ComplianceAssessment | null>(null);
  const [validationRules, setValidationRules] = useState<ValidationRule[]>([]);
  const [cfrStatus, setCfrStatus] = useState<CFRPart11Status | null>(null);
  const [isoStatus, setIsoStatus] = useState<ISO13485Status | null>(null);
  const [auditTrail, setAuditTrail] = useState<AuditTrailEntry[]>([]);

  // Dialog state
  const [showValidationDialog, setShowValidationDialog] = useState(false);
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [selectedModules, setSelectedModules] = useState<string[]>(['edms', 'training', 'quality', 'lims']);

  useEffect(() => {
    loadComplianceData();
  }, []);

  const loadComplianceData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [dashboard, assessment, rules, cfr, iso, audit] = await Promise.all([
        complianceService.getComplianceDashboard(),
        complianceService.getComplianceAssessment(['edms', 'training', 'quality', 'lims']),
        complianceService.getValidationRules(),
        complianceService.getCFRPart11Status(),
        complianceService.getISO13485Status(),
        complianceService.getAuditTrail(undefined, undefined, undefined, 
          new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          new Date().toISOString(),
          50
        )
      ]);

      setDashboardData(dashboard);
      setComplianceAssessment(assessment);
      setValidationRules(rules);
      setCfrStatus(cfr);
      setIsoStatus(iso);
      setAuditTrail(audit.entries);

    } catch (err) {
      setError('Failed to load compliance data. Please try again.');
      console.error('Compliance data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleRunValidation = async () => {
    try {
      setLoading(true);
      const result = await complianceService.runComplianceValidation(selectedModules);
      if (result.success) {
        setShowValidationDialog(false);
        // Reload data after validation
        await loadComplianceData();
      }
    } catch (err) {
      setError('Validation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setLoading(true);
      const result = await complianceService.generateComplianceReport(
        'comprehensive',
        'all',
        selectedModules,
        new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        new Date().toISOString()
      );
      if (result.success) {
        setShowReportDialog(false);
        // Show success message
      }
    } catch (err) {
      setError('Report generation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getComplianceColor = (score: number): string => {
    if (score >= 90) return '#4caf50';
    if (score >= 70) return '#ff9800';
    return '#f44336';
  };

  const getStatusChip = (status: string, score?: number) => {
    if (score !== undefined) {
      if (score >= 90) return <Chip label="Compliant" color="success" size="small" />;
      if (score >= 70) return <Chip label="Warning" color="warning" size="small" />;
      return <Chip label="Non-Compliant" color="error" size="small" />;
    }

    switch (status.toLowerCase()) {
      case 'compliant':
      case 'ready':
      case 'passed':
        return <Chip label={status} color="success" size="small" />;
      case 'warning':
      case 'needs_attention':
        return <Chip label={status} color="warning" size="small" />;
      case 'non_compliant':
      case 'failed':
      case 'critical':
        return <Chip label={status} color="error" size="small" />;
      default:
        return <Chip label={status} color="default" size="small" />;
    }
  };

  const complianceModuleData = complianceAssessment ? 
    Object.entries(complianceAssessment.module_scores).map(([module, score]) => ({
      module: module.toUpperCase(),
      score,
      status: score >= 90 ? 'Compliant' : score >= 70 ? 'Warning' : 'Non-Compliant'
    })) : [];

  if (loading && !dashboardData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} />
        <Typography sx={{ ml: 2 }}>Loading Compliance Dashboard...</Typography>
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
              Compliance Automation Dashboard
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Automated Regulatory Compliance Monitoring & Validation
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<PlayArrowIcon />}
              onClick={() => setShowValidationDialog(true)}
              color="primary"
            >
              Run Validation
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => setShowReportDialog(true)}
            >
              Generate Report
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadComplianceData}
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
            <Tab label="Overview" icon={<SecurityIcon />} />
            <Tab label="CFR Part 11" icon={<ShieldIcon />} />
            <Tab label="ISO 13485" icon={<VerifiedUserIcon />} />
            <Tab label="Audit Trail" icon={<AssignmentIcon />} />
            <Tab label="Validation Rules" icon={<GavelIcon />} />
            <Tab label="Reports" icon={<AssessmentIcon />} />
          </Tabs>
        </Paper>

        {/* Overview Tab */}
        <TabPanel value={activeTab} index={0}>
          {dashboardData && complianceAssessment && (
            <Grid container spacing={3}>
              {/* Overall Compliance Score */}
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" gutterBottom>
                      Overall Compliance Score
                    </Typography>
                    <Box sx={{ position: 'relative', display: 'inline-flex', mb: 2 }}>
                      <CircularProgress
                        variant="determinate"
                        value={dashboardData.overall_compliance}
                        size={120}
                        thickness={4}
                        sx={{ color: getComplianceColor(dashboardData.overall_compliance) }}
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
                          {Math.round(dashboardData.overall_compliance)}%
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Audit Readiness: {complianceAssessment.audit_readiness}
                    </Typography>
                    {getStatusChip(complianceAssessment.audit_readiness)}
                  </CardContent>
                </Card>
              </Grid>

              {/* Module Compliance Breakdown */}
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Module Compliance Breakdown
                    </Typography>
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={complianceModuleData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="module" />
                          <YAxis domain={[0, 100]} />
                          <Tooltip />
                          <Bar dataKey="score" fill="#2196f3" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Critical Issues */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <ErrorIcon sx={{ mr: 1, color: 'error.main' }} />
                      Critical Issues ({complianceAssessment.critical_issues.length})
                    </Typography>
                    {complianceAssessment.critical_issues.length > 0 ? (
                      complianceAssessment.critical_issues.map((issue, index) => (
                        <Alert key={index} severity="error" sx={{ mb: 1 }}>
                          {issue}
                        </Alert>
                      ))
                    ) : (
                      <Alert severity="success">
                        No critical issues identified
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Recommendations */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <CheckCircleIcon sx={{ mr: 1, color: 'info.main' }} />
                      Recommendations ({complianceAssessment.recommendations.length})
                    </Typography>
                    {complianceAssessment.recommendations.map((rec, index) => (
                      <Alert key={index} severity="info" sx={{ mb: 1 }}>
                        {rec}
                      </Alert>
                    ))}
                  </CardContent>
                </Card>
              </Grid>

              {/* Regulation Status */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Regulation Compliance Status
                    </Typography>
                    <Grid container spacing={2}>
                      {Object.entries(dashboardData.regulation_status).map(([regulation, status]) => (
                        <Grid item xs={12} sm={6} md={3} key={regulation}>
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <Typography variant="subtitle2" gutterBottom>
                              {regulation.toUpperCase()}
                            </Typography>
                            <Typography variant="h6">
                              {typeof status === 'object' ? (status as any).score : status}%
                            </Typography>
                            {getStatusChip('', typeof status === 'object' ? (status as any).score : status)}
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* CFR Part 11 Tab */}
        <TabPanel value={activeTab} index={1}>
          {cfrStatus && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      CFR Part 11 Compliance
                    </Typography>
                    <Typography variant="h3" sx={{ color: getComplianceColor(cfrStatus.overall_compliance) }}>
                      {Math.round(cfrStatus.overall_compliance)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Electronic Records & Signatures
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      CFR Part 11 Components
                    </Typography>
                    {Object.entries(cfrStatus).filter(([key]) => 
                      !['regulation', 'overall_compliance', 'findings', 'recommendations', 'last_assessment'].includes(key)
                    ).map(([component, data]) => (
                      <Accordion key={component}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography variant="subtitle1">
                            {component.replace(/_/g, ' ').toUpperCase()}
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <pre>{JSON.stringify(data, null, 2)}</pre>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      CFR Part 11 Findings & Recommendations
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" gutterBottom>Findings:</Typography>
                        {cfrStatus.findings.map((finding, index) => (
                          <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                            {finding}
                          </Alert>
                        ))}
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" gutterBottom>Recommendations:</Typography>
                        {cfrStatus.recommendations.map((rec, index) => (
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

        {/* ISO 13485 Tab */}
        <TabPanel value={activeTab} index={2}>
          {isoStatus && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      ISO 13485 Compliance
                    </Typography>
                    <Typography variant="h3" sx={{ color: getComplianceColor(isoStatus.overall_compliance) }}>
                      {Math.round(isoStatus.overall_compliance)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Quality Management System
                    </Typography>
                    <Chip 
                      label={isoStatus.certification_status} 
                      color={isoStatus.certification_status === 'certified' ? 'success' : 'warning'}
                      sx={{ mt: 1 }}
                    />
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      ISO 13485 Process Areas
                    </Typography>
                    {Object.entries(isoStatus).filter(([key]) => 
                      !['regulation', 'overall_compliance', 'findings', 'recommendations', 'certification_status'].includes(key)
                    ).map(([process, data]) => (
                      <Accordion key={process}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography variant="subtitle1">
                            {process.replace(/_/g, ' ').toUpperCase()}
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <pre>{JSON.stringify(data, null, 2)}</pre>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* Audit Trail Tab */}
        <TabPanel value={activeTab} index={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Audit Trail (Last 7 Days)
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>User</TableCell>
                      <TableCell>Module</TableCell>
                      <TableCell>Action</TableCell>
                      <TableCell>Entity</TableCell>
                      <TableCell>IP Address</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {auditTrail.map((entry) => (
                      <TableRow key={entry.entry_id}>
                        <TableCell>{new Date(entry.timestamp).toLocaleString()}</TableCell>
                        <TableCell>{entry.user_id}</TableCell>
                        <TableCell>
                          <Chip label={entry.module} size="small" />
                        </TableCell>
                        <TableCell>{entry.action}</TableCell>
                        <TableCell>{entry.entity_type} #{entry.entity_id}</TableCell>
                        <TableCell>{entry.ip_address}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Validation Rules Tab */}
        <TabPanel value={activeTab} index={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Validation Rules ({validationRules.length})
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Rule Name</TableCell>
                      <TableCell>Regulation</TableCell>
                      <TableCell>Module</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Automated</TableCell>
                      <TableCell>Frequency</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {validationRules.map((rule) => (
                      <TableRow key={rule.rule_id}>
                        <TableCell>{rule.rule_name}</TableCell>
                        <TableCell>
                          <Chip label={rule.regulation} size="small" />
                        </TableCell>
                        <TableCell>
                          <Chip label={rule.module} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={rule.severity} 
                            size="small"
                            color={rule.severity === 'critical' ? 'error' : rule.severity === 'high' ? 'warning' : 'default'}
                          />
                        </TableCell>
                        <TableCell>
                          {rule.automated ? <CheckCircleIcon color="success" /> : <ErrorIcon color="disabled" />}
                        </TableCell>
                        <TableCell>{rule.check_frequency}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Reports Tab */}
        <TabPanel value={activeTab} index={5}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Compliance Reports
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Generate comprehensive compliance reports for regulatory submissions and internal audits.
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<DownloadIcon />}
                    onClick={() => setShowReportDialog(true)}
                  >
                    Generate New Report
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Validation Dialog */}
        <Dialog open={showValidationDialog} onClose={() => setShowValidationDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Run Compliance Validation</DialogTitle>
          <DialogContent>
            <Typography variant="body2" paragraph>
              Select modules to validate for compliance rules and regulations.
            </Typography>
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Modules</InputLabel>
              <Select
                multiple
                value={selectedModules}
                onChange={(e) => setSelectedModules(e.target.value as string[])}
                label="Modules"
              >
                <MenuItem value="edms">EDMS</MenuItem>
                <MenuItem value="training">Training</MenuItem>
                <MenuItem value="quality">Quality</MenuItem>
                <MenuItem value="lims">LIMS</MenuItem>
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowValidationDialog(false)}>Cancel</Button>
            <Button onClick={handleRunValidation} variant="contained" disabled={loading}>
              {loading ? <CircularProgress size={24} /> : 'Run Validation'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Report Generation Dialog */}
        <Dialog open={showReportDialog} onClose={() => setShowReportDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Generate Compliance Report</DialogTitle>
          <DialogContent>
            <Typography variant="body2" paragraph>
              Generate a comprehensive compliance report for the selected modules and time period.
            </Typography>
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Modules</InputLabel>
              <Select
                multiple
                value={selectedModules}
                onChange={(e) => setSelectedModules(e.target.value as string[])}
                label="Modules"
              >
                <MenuItem value="edms">EDMS</MenuItem>
                <MenuItem value="training">Training</MenuItem>
                <MenuItem value="quality">Quality</MenuItem>
                <MenuItem value="lims">LIMS</MenuItem>
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowReportDialog(false)}>Cancel</Button>
            <Button onClick={handleGenerateReport} variant="contained" disabled={loading}>
              {loading ? <CircularProgress size={24} /> : 'Generate Report'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
};

export default ComplianceDashboard;