// QMS Department Role Matrix Component - Phase A Sprint 2 Day 9 (Simplified)
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Switch,
  FormControlLabel,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Security as SecurityIcon,
  Group as GroupIcon
} from '@mui/icons-material';
import { DepartmentRole } from '../../types/organization';
import organizationService from '../../services/organizationService';

interface User {
  id: number;
  full_name: string;
  job_title?: string;
  department?: string;
}

interface Role {
  id: number;
  name: string;
  display_name: string;
  permissions: string[];
}

const DepartmentRoleMatrix: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [assignments, setAssignments] = useState<DepartmentRole[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data for demonstration
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Mock users data
        const mockUsers: User[] = [
          { id: 1, full_name: 'John Doe', job_title: 'Quality Manager', department: 'Quality Assurance' },
          { id: 2, full_name: 'Jane Smith', job_title: 'Lab Technician', department: 'Laboratory' },
          { id: 3, full_name: 'Bob Johnson', job_title: 'Production Supervisor', department: 'Manufacturing' },
          { id: 4, full_name: 'Alice Brown', job_title: 'QA Analyst', department: 'Quality Assurance' },
        ];

        // Mock roles data
        const mockRoles: Role[] = [
          { id: 1, name: 'quality_manager', display_name: 'Quality Manager', permissions: ['quality.manage', 'documents.approve'] },
          { id: 2, name: 'lab_technician', display_name: 'Lab Technician', permissions: ['lims.execute', 'samples.test'] },
          { id: 3, name: 'supervisor', display_name: 'Supervisor', permissions: ['users.manage', 'reports.view'] },
          { id: 4, name: 'analyst', display_name: 'Analyst', permissions: ['data.view', 'reports.create'] },
        ];

        // Mock assignments data
        const mockAssignments: DepartmentRole[] = [];

        setUsers(mockUsers);
        setRoles(mockRoles);
        setAssignments(mockAssignments);
      } catch (err) {
        setError('Failed to load role matrix data');
        console.error('Error loading data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const hasAssignment = (userId: number, roleId: number): boolean => {
    return assignments.some(assignment => 
      assignment.user_id === userId && assignment.role_id === roleId && assignment.is_active
    );
  };

  const toggleAssignment = async (userId: number, roleId: number) => {
    try {
      const hasRole = hasAssignment(userId, roleId);
      
      if (hasRole) {
        // Remove assignment
        setAssignments(prev => prev.filter(assignment => 
          !(assignment.user_id === userId && assignment.role_id === roleId)
        ));
      } else {
        // Add assignment
        const newAssignment: DepartmentRole = {
          id: Date.now(), // Mock ID
          department_id: 1, // Mock department
          role_id: roleId,
          user_id: userId,
          valid_from: new Date().toISOString(),
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          department: {
            id: 1,
            uuid: 'mock-uuid',
            name: 'Mock Department',
            department_type: 'operational',
            hierarchy_level: 0,
            is_active: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          },
          role: {
            id: roleId,
            name: roles.find(r => r.id === roleId)?.name || '',
            display_name: roles.find(r => r.id === roleId)?.display_name || '',
            permissions: roles.find(r => r.id === roleId)?.permissions || []
          },
          user: {
            id: userId,
            full_name: users.find(u => u.id === userId)?.full_name || '',
            job_title: users.find(u => u.id === userId)?.job_title
          }
        };
        setAssignments(prev => [...prev, newAssignment]);
      }
    } catch (err) {
      setError('Failed to update role assignment');
      console.error('Error updating assignment:', err);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Department Role Matrix</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          disabled
        >
          Bulk Assign
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <SecurityIcon color="primary" />
            <Typography variant="h6">Role Assignments</Typography>
          </Box>

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <GroupIcon />
                      <strong>User</strong>
                    </Box>
                  </TableCell>
                  <TableCell><strong>Department</strong></TableCell>
                  {roles.map(role => (
                    <TableCell key={role.id} align="center">
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <strong>{role.display_name}</strong>
                        <Chip 
                          label={`${role.permissions.length} permissions`}
                          size="small"
                          variant="outlined"
                          sx={{ mt: 0.5 }}
                        />
                      </Box>
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map(user => (
                  <TableRow key={user.id} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="subtitle2">{user.full_name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {user.job_title}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={user.department || 'Unassigned'} 
                        size="small"
                        color={user.department ? 'primary' : 'default'}
                        variant="outlined"
                      />
                    </TableCell>
                    {roles.map(role => (
                      <TableCell key={role.id} align="center">
                        <FormControlLabel
                          control={
                            <Switch
                              checked={hasAssignment(user.id, role.id)}
                              onChange={() => toggleAssignment(user.id, role.id)}
                              size="small"
                            />
                          }
                          label=""
                          sx={{ m: 0 }}
                        />
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {assignments.length} active role assignments
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {roles.map(role => (
                <Chip
                  key={role.id}
                  label={`${role.display_name}: ${assignments.filter(a => a.role_id === role.id).length}`}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default DepartmentRoleMatrix;