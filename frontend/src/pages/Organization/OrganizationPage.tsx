// Organization Management Page - Phase A Sprint 2 Day 9
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Paper,
  Container
} from '@mui/material';
import {
  Business as BusinessIcon,
  AccountTree as HierarchyIcon,
  Security as RoleIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';

import DepartmentHierarchy from '../../components/Organization/DepartmentHierarchy_Simple';
import DepartmentRoleMatrix from '../../components/Organization/DepartmentRoleMatrix_Simple';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`organization-tabpanel-${index}`}
      aria-labelledby={`organization-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const OrganizationPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Organization Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage department hierarchies, role assignments, and organizational structure
        </Typography>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="organization management tabs"
            variant="fullWidth"
          >
            <Tab
              icon={<HierarchyIcon />}
              label="Department Hierarchy"
              id="organization-tab-0"
              aria-controls="organization-tabpanel-0"
            />
            <Tab
              icon={<RoleIcon />}
              label="Role Matrix"
              id="organization-tab-1"
              aria-controls="organization-tabpanel-1"
            />
            <Tab
              icon={<AnalyticsIcon />}
              label="Analytics"
              id="organization-tab-2"
              aria-controls="organization-tabpanel-2"
            />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <DepartmentHierarchy />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <DepartmentRoleMatrix />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Organization Analytics
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Analytics dashboard coming in Phase B - Advanced Reporting & Analytics
            </Typography>
          </Box>
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default OrganizationPage;