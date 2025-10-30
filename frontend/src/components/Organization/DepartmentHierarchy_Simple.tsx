// QMS Department Hierarchy Component - Phase A Sprint 2 Day 9 (Simplified)
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Business as BusinessIcon,
  Group as GroupIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { DepartmentNode } from '../../types/organization';
import organizationService from '../../services/organizationService';

const DepartmentHierarchy: React.FC = () => {
  const [hierarchyData, setHierarchyData] = useState<DepartmentNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<DepartmentNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    department_type: 'operational' as 'operational' | 'administrative' | 'quality',
    location: '',
    parent_department_id: undefined as number | undefined
  });

  // Load hierarchy data
  const loadHierarchy = async () => {
    try {
      setLoading(true);
      setError(null);
      // Use integration test backend on port 8001
      const response = await fetch('http://localhost:8001/v1/organization/departments/hierarchy');
      const result = await response.json();
      if (result.success) {
        setHierarchyData(result.data);
      } else {
        throw new Error(result.message || 'Failed to load hierarchy');
      }
    } catch (err) {
      setError('Failed to load department hierarchy');
      console.error('Error loading hierarchy:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHierarchy();
  }, []);

  const handleCreateDepartment = async () => {
    try {
      const response = await fetch('http://localhost:8001/v1/organization/departments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      const result = await response.json();
      if (result.success) {
        setCreateDialogOpen(false);
        setFormData({
          name: '',
          description: '',
          department_type: 'operational',
          location: '',
          parent_department_id: undefined
        });
        await loadHierarchy();
      } else {
        throw new Error(result.message || 'Failed to create department');
      }
    } catch (err) {
      setError('Failed to create department');
      console.error('Error creating department:', err);
    }
  };

  const renderDepartmentCard = (department: DepartmentNode, level: number = 0) => (
    <Box key={department.id} sx={{ ml: level * 3, mb: 1 }}>
      <Card 
        variant="outlined" 
        sx={{ 
          cursor: 'pointer',
          '&:hover': { backgroundColor: 'action.hover' }
        }}
        onClick={() => setSelectedNode(department)}
      >
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BusinessIcon color="primary" />
              <Typography variant="subtitle1" fontWeight="bold">
                {department.name}
              </Typography>
              <Chip 
                label={department.department_type} 
                size="small" 
                color="primary"
                variant="outlined"
              />
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip 
                icon={<GroupIcon />}
                label={`${department.user_count || 0} users`}
                size="small"
              />
              <IconButton size="small">
                <EditIcon />
              </IconButton>
            </Box>
          </Box>
          
          {department.department_head && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              <PersonIcon fontSize="small" />
              <Typography variant="body2" color="text.secondary">
                Head: {department.department_head.full_name}
              </Typography>
            </Box>
          )}
          
          {department.location && (
            <Typography variant="body2" color="text.secondary">
              Location: {department.location}
            </Typography>
          )}
        </CardContent>
      </Card>
      
      {/* Render children */}
      {department.children && department.children.map(child => 
        renderDepartmentCard(child, level + 1)
      )}
    </Box>
  );

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
        <Typography variant="h5">Department Hierarchy</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Add Department
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 3 }}>
        <Box sx={{ flex: 2 }}>
          {hierarchyData.length === 0 ? (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <BusinessIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  No Departments Yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Create your first department to get started
                </Typography>
              </CardContent>
            </Card>
          ) : (
            hierarchyData.map(department => renderDepartmentCard(department))
          )}
        </Box>

        {selectedNode && (
          <Box sx={{ flex: 1 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Department Details
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="Name" 
                      secondary={selectedNode.name} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Type" 
                      secondary={selectedNode.department_type} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Level" 
                      secondary={selectedNode.hierarchy_level} 
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="User Count" 
                      secondary={selectedNode.user_count || 0} 
                    />
                  </ListItem>
                  {selectedNode.location && (
                    <ListItem>
                      <ListItemText 
                        primary="Location" 
                        secondary={selectedNode.location} 
                      />
                    </ListItem>
                  )}
                </List>
              </CardContent>
            </Card>
          </Box>
        )}
      </Box>

      {/* Create Department Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Department</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Department Name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              fullWidth
              required
            />
            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              fullWidth
              multiline
              rows={3}
            />
            <FormControl fullWidth>
              <InputLabel>Department Type</InputLabel>
              <Select
                value={formData.department_type}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  department_type: e.target.value as 'operational' | 'administrative' | 'quality'
                }))}
                label="Department Type"
              >
                <MenuItem value="operational">Operational</MenuItem>
                <MenuItem value="administrative">Administrative</MenuItem>
                <MenuItem value="quality">Quality</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Location"
              value={formData.location}
              onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateDepartment} 
            variant="contained"
            disabled={!formData.name}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DepartmentHierarchy;