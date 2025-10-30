// QMS Department Role Matrix Component - Phase A Sprint 2 Day 9
// Role assignment matrix with bulk operations and filtering

import { DepartmentRole, AssignRoleRequest, BulkRoleAssignmentRequest } from '../../types/organization';
import organizationService from '../../services/organizationService';
// Interactive role assignment matrix with drag-and-drop functionality

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  CircularProgress,
  Alert,
  Autocomplete,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Security as SecurityIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridRowSelectionModel } from '@mui/x-data-grid';
// import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Types
interface User {
  id: number;
  full_name: string;
  username: string;
  email: string;
  job_title?: string;
  department_id: number;
  department_name: string;
  profile_picture_url?: string;
  is_active: boolean;
}

interface Role {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  permissions: string[];
  is_active: boolean;
}

interface Department {
  id: number;
  name: string;
  code?: string;
  department_type?: string;
  hierarchy_level: number;
  user_count: number;
}

interface DepartmentRoleAssignment {
  id: number;
  department_id: number;
  role_id: number;
  user_id: number;
  assigned_by?: number;
  valid_from: string;
  valid_until?: string;
  is_active: boolean;
  department_name?: string;
  role_name?: string;
  user_name?: string;
  days_until_expiry?: number;
}

interface RoleAssignmentRequest {
  valid_from?: string;
  valid_until?: string;
  comment?: string;
}

const DepartmentRoleMatrix: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [assignments, setAssignments] = useState<DepartmentRoleAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [showInactiveAssignments, setShowInactiveAssignments] = useState(false);
  const [showExpiringOnly, setShowExpiringOnly] = useState(false);

  // Dialog states
  const [assignmentDialogOpen, setAssignmentDialogOpen] = useState(false);
  const [bulkAssignmentDialogOpen, setBulkAssignmentDialogOpen] = useState(false);
  const [selectedUsers, setSelectedUsers] = useState<GridRowSelectionModel>([]);

  // Assignment form data
  const [assignmentForm, setAssignmentForm] = useState<{
    user_id: number;
    department_id: number;
    role_id: number;
    assignment_data: RoleAssignmentRequest;
  }>({
    user_id: 0,
    department_id: 0,
    role_id: 0,
    assignment_data: {}
  });

  // Load data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      
      const [usersRes, rolesRes, departmentsRes, assignmentsRes] = await Promise.all([
        fetch('/api/v1/users/'),
        fetch('/api/v1/roles/'),
        fetch('/api/v1/org/organizations/1/departments/hierarchy'),
        fetch('/api/v1/org/departments/role-assignments')
      ]);

      const [usersData, rolesData, departmentsData, assignmentsData] = await Promise.all([
        usersRes.json(),
        rolesRes.json(),
        departmentsRes.json(),
        assignmentsRes.json()
      ]);

      setUsers(usersData);
      setRoles(rolesData);
      setDepartments(flattenDepartments(departmentsData));
      setAssignments(assignmentsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Flatten hierarchical departments
  const flattenDepartments = (hierarchyData: any[]): Department[] => {
    const flattened: Department[] = [];
    
    const flatten = (nodes: any[]) => {
      nodes.forEach(node => {
        flattened.push({
          id: node.id,
          name: node.name,
          code: node.code,
          department_type: node.department_type,
          hierarchy_level: node.hierarchy_level,
          user_count: node.user_count
        });
        if (node.children) {
          flatten(node.children);
        }
      });
    };
    
    flatten(hierarchyData);
    return flattened;
  };

  // Filter users based on selected department
  const filteredUsers = users.filter(user => {
    if (selectedDepartment && user.department_id !== selectedDepartment.id) {
      return false;
    }
    return true;
  });

  // Filter assignments
  const filteredAssignments = assignments.filter(assignment => {
    if (!showInactiveAssignments && !assignment.is_active) {
      return false;
    }
    if (selectedDepartment && assignment.department_id !== selectedDepartment.id) {
      return false;
    }
    if (selectedRole && assignment.role_id !== selectedRole.id) {
      return false;
    }
    if (showExpiringOnly && (!assignment.days_until_expiry || assignment.days_until_expiry > 30)) {
      return false;
    }
    return true;
  });

  // Get user assignments for a specific role and department
  const getUserAssignment = (userId: number, roleId: number, departmentId?: number) => {
    return filteredAssignments.find(
      assignment => 
        assignment.user_id === userId && 
        assignment.role_id === roleId &&
        (!departmentId || assignment.department_id === departmentId) &&
        assignment.is_active
    );
  };

  // Assign role to user
  const assignRole = async (userId: number, departmentId: number, roleId: number, assignmentData: RoleAssignmentRequest) => {
    try {
      const response = await fetch(
        `/api/v1/org/departments/${departmentId}/roles/${roleId}/assign/${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(assignmentData)
        }
      );

      if (!response.ok) throw new Error('Failed to assign role');
      
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign role');
    }
  };

  // Revoke role assignment
  const revokeRole = async (assignmentId: number) => {
    try {
      const response = await fetch(`/api/v1/org/department-roles/${assignmentId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to revoke role');
      
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke role');
    }
  };

  // Handle role assignment cell click
  const handleRoleToggle = (user: User, role: Role, department: Department) => {
    const assignment = getUserAssignment(user.id, role.id, department.id);
    
    if (assignment) {
      revokeRole(assignment.id);
    } else {
      setAssignmentForm({
        user_id: user.id,
        department_id: department.id,
        role_id: role.id,
        assignment_data: {}
      });
      setAssignmentDialogOpen(true);
    }
  };

  // Handle bulk assignment
  const handleBulkAssignment = () => {
    if (selectedUsers.length === 0) {
      setError('Please select users for bulk assignment');
      return;
    }
    setBulkAssignmentDialogOpen(true);
  };

  // Columns for DataGrid
  const columns: GridColDef[] = [
    {
      field: 'full_name',
      headerName: 'User',
      width: 200,
      renderCell: (params) => (
        <Box display="flex" alignItems="center" gap={1}>
          <Avatar 
            src={params.row.profile_picture_url}
            sx={{ width: 32, height: 32 }}
          >
            <PersonIcon />
          </Avatar>
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {params.value}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {params.row.job_title}
            </Typography>
          </Box>
        </Box>
      )
    },
    {
      field: 'department_name',
      headerName: 'Department',
      width: 150,
      renderCell: (params) => (
        <Chip 
          label={params.value} 
          size="small" 
          variant="outlined"
          icon={<BusinessIcon />}
        />
      )
    },
    ...roles.map(role => ({
      field: `role_${role.id}`,
      headerName: role.display_name,
      width: 120,
      sortable: false,
      renderCell: (params: any) => {
        const user = params.row;
        const department = selectedDepartment || departments.find(d => d.id === user.department_id);
        if (!department) return null;

        const assignment = getUserAssignment(user.id, role.id, department.id);
        
        return (
          <RoleAssignmentCell
            user={user}
            role={role}
            department={department}
            assignment={assignment}
            onToggle={() => handleRoleToggle(user, role, department)}
          />
        );
      }
    }))
  ];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading role matrix...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Department Role Matrix
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            disabled={selectedUsers.length === 0}
            onClick={handleBulkAssignment}
          >
            Bulk Assign ({selectedUsers.length})
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => {/* Export functionality */}}
          >
            Export
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Box display="flex" gap={2} mb={3} p={2} bgcolor="grey.50" borderRadius={1}>
        <Autocomplete
          options={departments}
          getOptionLabel={(option) => `${option.name} (Level ${option.hierarchy_level})`}
          value={selectedDepartment}
          onChange={(_, value) => setSelectedDepartment(value)}
          renderInput={(params) => (
            <TextField {...params} label="Filter by Department" variant="outlined" />
          )}
          sx={{ minWidth: 250 }}
        />

        <Autocomplete
          options={roles}
          getOptionLabel={(option) => option.display_name}
          value={selectedRole}
          onChange={(_, value) => setSelectedRole(value)}
          renderInput={(params) => (
            <TextField {...params} label="Filter by Role" variant="outlined" />
          )}
          sx={{ minWidth: 200 }}
        />

        <FormControlLabel
          control={
            <Switch
              checked={showInactiveAssignments}
              onChange={(e) => setShowInactiveAssignments(e.target.checked)}
            />
          }
          label="Show Inactive"
        />

        <FormControlLabel
          control={
            <Switch
              checked={showExpiringOnly}
              onChange={(e) => setShowExpiringOnly(e.target.checked)}
            />
          }
          label="Expiring Soon"
        />
      </Box>

      {/* Statistics */}
      <Box display="flex" gap={3} mb={3}>
        <Box textAlign="center" p={2} bgcolor="primary.light" color="white" borderRadius={1}>
          <Typography variant="h4">{filteredUsers.length}</Typography>
          <Typography variant="body2">Users</Typography>
        </Box>
        <Box textAlign="center" p={2} bgcolor="secondary.light" color="white" borderRadius={1}>
          <Typography variant="h4">{roles.length}</Typography>
          <Typography variant="body2">Roles</Typography>
        </Box>
        <Box textAlign="center" p={2} bgcolor="success.light" color="white" borderRadius={1}>
          <Typography variant="h4">{filteredAssignments.length}</Typography>
          <Typography variant="body2">Active Assignments</Typography>
        </Box>
        <Box textAlign="center" p={2} bgcolor="warning.light" color="white" borderRadius={1}>
          <Typography variant="h4">
            {filteredAssignments.filter(a => a.days_until_expiry && a.days_until_expiry <= 30).length}
          </Typography>
          <Typography variant="body2">Expiring Soon</Typography>
        </Box>
      </Box>

      {/* Role Matrix */}
      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={filteredUsers}
          columns={columns}
          pageSize={25}
          rowsPerPageOptions={[10, 25, 50, 100]}
          checkboxSelection
          disableSelectionOnClick
          onSelectionModelChange={setSelectedUsers}
          density="compact"
          sx={{
            '& .MuiDataGrid-cell': {
              borderRight: '1px solid #f0f0f0'
            },
            '& .MuiDataGrid-columnHeaders': {
              backgroundColor: '#f5f5f5',
              borderBottom: '2px solid #e0e0e0'
            }
          }}
        />
      </Paper>

      {/* Assignment Dialog */}
      <AssignmentDialog
        open={assignmentDialogOpen}
        form={assignmentForm}
        onFormChange={setAssignmentForm}
        onSubmit={async () => {
          await assignRole(
            assignmentForm.user_id,
            assignmentForm.department_id,
            assignmentForm.role_id,
            assignmentForm.assignment_data
          );
          setAssignmentDialogOpen(false);
        }}
        onCancel={() => setAssignmentDialogOpen(false)}
        users={users}
        roles={roles}
        departments={departments}
      />

      {/* Bulk Assignment Dialog */}
      <BulkAssignmentDialog
        open={bulkAssignmentDialogOpen}
        selectedUsers={selectedUsers.map(id => users.find(u => u.id === id)!).filter(Boolean)}
        onClose={() => setBulkAssignmentDialogOpen(false)}
        onSubmit={loadData}
        roles={roles}
        departments={departments}
      />
    </Box>
  );
};

// Role Assignment Cell Component
interface RoleAssignmentCellProps {
  user: User;
  role: Role;
  department: Department;
  assignment?: DepartmentRoleAssignment;
  onToggle: () => void;
}

const RoleAssignmentCell: React.FC<RoleAssignmentCellProps> = ({
  assignment,
  onToggle
}) => {
  const isAssigned = !!assignment;
  const isExpiring = assignment?.days_until_expiry && assignment.days_until_expiry <= 30;

  return (
    <Box display="flex" alignItems="center" justifyContent="center">
      <IconButton
        size="small"
        onClick={onToggle}
        sx={{
          backgroundColor: isAssigned ? 'success.main' : 'grey.300',
          color: isAssigned ? 'white' : 'grey.600',
          '&:hover': {
            backgroundColor: isAssigned ? 'success.dark' : 'grey.400'
          },
          ...(isExpiring && {
            backgroundColor: 'warning.main',
            '&:hover': { backgroundColor: 'warning.dark' }
          })
        }}
      >
        {isAssigned ? <SecurityIcon fontSize="small" /> : <AddIcon fontSize="small" />}
      </IconButton>
      
      {isExpiring && (
        <Tooltip title={`Expires in ${assignment?.days_until_expiry} days`}>
          <ScheduleIcon fontSize="small" color="warning" sx={{ ml: 0.5 }} />
        </Tooltip>
      )}
    </Box>
  );
};

// Assignment Dialog Component
interface AssignmentDialogProps {
  open: boolean;
  form: any;
  onFormChange: (form: any) => void;
  onSubmit: () => void;
  onCancel: () => void;
  users: User[];
  roles: Role[];
  departments: Department[];
}

const AssignmentDialog: React.FC<AssignmentDialogProps> = ({
  open,
  form,
  onFormChange,
  onSubmit,
  onCancel
}) => {
  return (
    <Dialog open={open} onClose={onCancel} maxWidth="md" fullWidth>
      <DialogTitle>Assign Department Role</DialogTitle>
      <DialogContent>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <DatePicker
              label="Valid From"
              value={form.assignment_data.valid_from ? new Date(form.assignment_data.valid_from) : null}
              onChange={(date) => onFormChange({
                ...form,
                assignment_data: {
                  ...form.assignment_data,
                  valid_from: date?.toISOString()
                }
              })}
              renderInput={(params) => <TextField {...params} fullWidth />}
            />
            
            <DatePicker
              label="Valid Until (Optional)"
              value={form.assignment_data.valid_until ? new Date(form.assignment_data.valid_until) : null}
              onChange={(date) => onFormChange({
                ...form,
                assignment_data: {
                  ...form.assignment_data,
                  valid_until: date?.toISOString()
                }
              })}
              renderInput={(params) => <TextField {...params} fullWidth />}
            />
            
            <TextField
              label="Comment (Optional)"
              value={form.assignment_data.comment || ''}
              onChange={(e) => onFormChange({
                ...form,
                assignment_data: {
                  ...form.assignment_data,
                  comment: e.target.value
                }
              })}
              multiline
              rows={2}
              fullWidth
            />
          </Box>
        </LocalizationProvider>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={onSubmit} variant="contained">Assign Role</Button>
      </DialogActions>
    </Dialog>
  );
};

// Bulk Assignment Dialog Component
interface BulkAssignmentDialogProps {
  open: boolean;
  selectedUsers: User[];
  onClose: () => void;
  onSubmit: () => void;
  roles: Role[];
  departments: Department[];
}

const BulkAssignmentDialog: React.FC<BulkAssignmentDialogProps> = ({
  open,
  selectedUsers,
  onClose,
  onSubmit
}) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Bulk Role Assignment</DialogTitle>
      <DialogContent>
        <Typography variant="body1" gutterBottom>
          Assign roles to {selectedUsers.length} selected users
        </Typography>
        
        <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
          {selectedUsers.map(user => (
            <Chip
              key={user.id}
              label={user.full_name}
              size="small"
              avatar={<Avatar src={user.profile_picture_url}><PersonIcon /></Avatar>}
            />
          ))}
        </Box>
        
        {/* Bulk assignment form would go here */}
        <Typography variant="body2" color="text.secondary">
          Bulk assignment functionality to be implemented
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onSubmit} variant="contained">Assign Roles</Button>
      </DialogActions>
    </Dialog>
  );
};

export default DepartmentRoleMatrix;