// QMS Department Hierarchy Component - Phase A Sprint 2 Day 9
// Interactive department hierarchy tree with drag-and-drop functionality

import React, { useState, useEffect, useCallback } from 'react';
import { TreeView } from '@mui/x-tree-view/TreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import {
  Box,
  Typography,
  Button,
  IconButton,
  Chip,
  Avatar,
  Tooltip,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Business as BusinessIcon,
  Group as GroupIcon,
  Person as PersonIcon,
  LocationOn as LocationIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
// Drag and drop functionality - will be implemented in future iteration
// import { DndProvider, useDrag, useDrop } from 'react-dnd';
// import { HTML5Backend } from 'react-dnd-html5-backend';

// Import types
import { DepartmentNode, Department, CreateDepartmentRequest, UpdateDepartmentRequest } from '../../types/organization';
import organizationService from '../../services/organizationService';

interface DepartmentFormData {
  name: string;
  code: string;
  description: string;
  department_type: string;
  location: string;
  cost_center: string;
  department_head_id?: number;
  parent_department_id?: number;
}

// Department Type Colors
const departmentTypeColors: Record<string, string> = {
  operational: '#1976d2',
  administrative: '#388e3c', 
  quality: '#f57c00',
  research: '#7b1fa2',
  regulatory: '#d32f2f'
};

const DepartmentHierarchy: React.FC = () => {
  const [hierarchyData, setHierarchyData] = useState<DepartmentNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<DepartmentNode | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [analyticsDialogOpen, setAnalyticsDialogOpen] = useState(false);
  
  // Form states
  const [formData, setFormData] = useState<DepartmentFormData>({
    name: '',
    code: '',
    description: '',
    department_type: 'operational',
    location: '',
    cost_center: '',
    department_head_id: undefined,
    parent_department_id: undefined
  });

  // Load hierarchy data
  const loadHierarchy = useCallback(async () => {
    try {
      setLoading(true);
      const data = await organizationService.getDepartmentHierarchy();
      setHierarchyData(data);
      
      // Auto-expand first level
      const firstLevelIds = data.map((node: DepartmentNode) => node.id.toString());
      setExpandedNodes(firstLevelIds);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHierarchy();
  }, [loadHierarchy]);

  // Handle node selection
  const handleNodeSelect = (nodeId: string) => {
    const findNode = (nodes: DepartmentNode[], id: number): DepartmentNode | null => {
      for (const node of nodes) {
        if (node.id === id) return node;
        const found = findNode(node.children, id);
        if (found) return found;
      }
      return null;
    };

    const node = findNode(hierarchyData, parseInt(nodeId));
    setSelectedNode(node);
  };

  // Handle node expansion
  const handleNodeToggle = (event: React.SyntheticEvent, nodeIds: string[]) => {
    setExpandedNodes(nodeIds);
  };

  // Create department
  const handleCreateDepartment = async () => {
    try {
      const response = await fetch('/api/v1/org/departments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          organization_id: 1,
          ...formData
        })
      });

      if (!response.ok) throw new Error('Failed to create department');
      
      await loadHierarchy();
      setCreateDialogOpen(false);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create department');
    }
  };

  // Update department
  const handleUpdateDepartment = async () => {
    if (!selectedNode) return;

    try {
      const response = await fetch(`/api/v1/org/departments/${selectedNode.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) throw new Error('Failed to update department');
      
      await loadHierarchy();
      setEditDialogOpen(false);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update department');
    }
  };

  // Delete department
  const handleDeleteDepartment = async () => {
    if (!selectedNode) return;

    try {
      const response = await fetch(`/api/v1/org/departments/${selectedNode.id}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete department');
      
      await loadHierarchy();
      setDeleteDialogOpen(false);
      setSelectedNode(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete department');
    }
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      name: '',
      code: '',
      description: '',
      department_type: 'operational',
      location: '',
      cost_center: '',
      department_head_id: undefined,
      parent_department_id: undefined
    });
  };

  // Open create dialog
  const openCreateDialog = (parentId?: number) => {
    resetForm();
    setFormData(prev => ({ ...prev, parent_department_id: parentId }));
    setCreateDialogOpen(true);
  };

  // Open edit dialog
  const openEditDialog = (node: DepartmentNode) => {
    setFormData({
      name: node.name,
      code: node.code || '',
      description: '',
      department_type: node.department_type || 'operational',
      location: node.location || '',
      cost_center: '',
      department_head_id: node.department_head?.id,
      parent_department_id: undefined
    });
    setSelectedNode(node);
    setEditDialogOpen(true);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading department hierarchy...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Button onClick={loadHierarchy} sx={{ ml: 2 }}>Retry</Button>
      </Alert>
    );
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            Department Hierarchy
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => openCreateDialog()}
          >
            Add Root Department
          </Button>
        </Box>

        {/* Main Content */}
        <Box display="flex" gap={3}>
          {/* Hierarchy Tree */}
          <Box flex={2}>
            <TreeView
              aria-label="department hierarchy"
              defaultCollapseIcon={<ExpandMoreIcon />}
              defaultExpandIcon={<ChevronRightIcon />}
              expanded={expandedNodes}
              onNodeToggle={handleNodeToggle}
              onNodeSelect={(event, nodeId) => handleNodeSelect(nodeId)}
              sx={{
                height: 600,
                flexGrow: 1,
                maxWidth: 400,
                overflowY: 'auto',
                border: '1px solid #e0e0e0',
                borderRadius: 1,
                p: 2
              }}
            >
              {hierarchyData.map(node => (
                <DepartmentTreeItem 
                  key={node.id} 
                  node={node} 
                  onEdit={openEditDialog}
                  onDelete={setSelectedNode}
                  onAddChild={openCreateDialog}
                />
              ))}
            </TreeView>
          </Box>

          {/* Department Details */}
          <Box flex={3}>
            {selectedNode ? (
              <DepartmentDetails 
                node={selectedNode}
                onEdit={() => openEditDialog(selectedNode)}
                onDelete={() => setDeleteDialogOpen(true)}
                onAddChild={() => openCreateDialog(selectedNode.id)}
                onShowAnalytics={() => setAnalyticsDialogOpen(true)}
              />
            ) : (
              <Box 
                display="flex" 
                flexDirection="column" 
                alignItems="center" 
                justifyContent="center"
                height={400}
                sx={{ 
                  border: '2px dashed #e0e0e0', 
                  borderRadius: 2,
                  color: 'text.secondary'
                }}
              >
                <BusinessIcon sx={{ fontSize: 64, mb: 2 }} />
                <Typography variant="h6">Select a department to view details</Typography>
                <Typography variant="body2">
                  Click on any department in the tree to see its information
                </Typography>
              </Box>
            )}
          </Box>
        </Box>

        {/* Create Department Dialog */}
        <DepartmentFormDialog
          open={createDialogOpen}
          title="Create Department"
          formData={formData}
          onFormDataChange={setFormData}
          onSubmit={handleCreateDepartment}
          onCancel={() => setCreateDialogOpen(false)}
        />

        {/* Edit Department Dialog */}
        <DepartmentFormDialog
          open={editDialogOpen}
          title="Edit Department"
          formData={formData}
          onFormDataChange={setFormData}
          onSubmit={handleUpdateDepartment}
          onCancel={() => setEditDialogOpen(false)}
        />

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
          <DialogTitle>Delete Department</DialogTitle>
          <DialogContent>
            <Typography>
              Are you sure you want to delete "{selectedNode?.name}"?
              {selectedNode?.children.length ? (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  This department has {selectedNode.children.length} child department(s).
                  They will also be deleted.
                </Alert>
              ) : null}
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleDeleteDepartment} color="error" variant="contained">
              Delete
            </Button>
          </DialogActions>
        </Dialog>

        {/* Analytics Dialog */}
        {selectedNode && (
          <DepartmentAnalyticsDialog
            open={analyticsDialogOpen}
            departmentId={selectedNode.id}
            departmentName={selectedNode.name}
            onClose={() => setAnalyticsDialogOpen(false)}
          />
        )}
      </Box>
    </DndProvider>
  );
};

// Department Tree Item Component
interface DepartmentTreeItemProps {
  node: DepartmentNode;
  onEdit: (node: DepartmentNode) => void;
  onDelete: (node: DepartmentNode) => void;
  onAddChild: (parentId: number) => void;
}

const DepartmentTreeItem: React.FC<DepartmentTreeItemProps> = ({
  node,
  onEdit,
  onDelete,
  onAddChild
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getDepartmentTypeIcon = (type?: string) => {
    switch (type) {
      case 'quality': return '🔬';
      case 'administrative': return '📋';
      case 'research': return '🧪';
      case 'regulatory': return '📜';
      default: return '🏭';
    }
  };

  return (
    <TreeItem
      nodeId={node.id.toString()}
      label={
        <Box display="flex" alignItems="center" py={0.5}>
          <Box display="flex" alignItems="center" flex={1}>
            <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
              {getDepartmentTypeIcon(node.department_type)} {node.name}
            </Typography>
            {node.code && (
              <Chip 
                label={node.code} 
                size="small" 
                sx={{ 
                  ml: 1, 
                  height: 20,
                  backgroundColor: departmentTypeColors[node.department_type || 'operational'],
                  color: 'white'
                }} 
              />
            )}
            <Chip 
              label={`${node.user_count} users`} 
              size="small" 
              variant="outlined"
              sx={{ ml: 1, height: 20 }} 
            />
          </Box>
          
          <IconButton
            size="small"
            onClick={handleMenuOpen}
            sx={{ ml: 1 }}
          >
            <MoreVertIcon fontSize="small" />
          </IconButton>

          <Menu
            anchorEl={anchorEl}
            open={menuOpen}
            onClose={handleMenuClose}
            onClick={(e) => e.stopPropagation()}
          >
            <MenuItem onClick={() => { onEdit(node); handleMenuClose(); }}>
              <EditIcon fontSize="small" sx={{ mr: 1 }} />
              Edit
            </MenuItem>
            <MenuItem onClick={() => { onAddChild(node.id); handleMenuClose(); }}>
              <AddIcon fontSize="small" sx={{ mr: 1 }} />
              Add Child
            </MenuItem>
            <MenuItem onClick={() => { onDelete(node); handleMenuClose(); }}>
              <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
              Delete
            </MenuItem>
          </Menu>
        </Box>
      }
    >
      {node.children.map(child => (
        <DepartmentTreeItem
          key={child.id}
          node={child}
          onEdit={onEdit}
          onDelete={onDelete}
          onAddChild={onAddChild}
        />
      ))}
    </TreeItem>
  );
};

// Department Details Component
interface DepartmentDetailsProps {
  node: DepartmentNode;
  onEdit: () => void;
  onDelete: () => void;
  onAddChild: () => void;
  onShowAnalytics: () => void;
}

const DepartmentDetails: React.FC<DepartmentDetailsProps> = ({
  node,
  onEdit,
  onDelete,
  onAddChild,
  onShowAnalytics
}) => {
  return (
    <Box sx={{ p: 3, border: '1px solid #e0e0e0', borderRadius: 2 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
        <Box>
          <Typography variant="h5" component="h2" gutterBottom>
            {node.name}
          </Typography>
          {node.code && (
            <Chip 
              label={node.code} 
              sx={{ 
                backgroundColor: departmentTypeColors[node.department_type || 'operational'],
                color: 'white',
                mb: 1
              }} 
            />
          )}
        </Box>
        
        <Box display="flex" gap={1}>
          <Button variant="outlined" size="small" startIcon={<EditIcon />} onClick={onEdit}>
            Edit
          </Button>
          <Button variant="outlined" size="small" startIcon={<AddIcon />} onClick={onAddChild}>
            Add Child
          </Button>
          <Button variant="outlined" size="small" startIcon={<AnalyticsIcon />} onClick={onShowAnalytics}>
            Analytics
          </Button>
          <Button variant="outlined" size="small" color="error" startIcon={<DeleteIcon />} onClick={onDelete}>
            Delete
          </Button>
        </Box>
      </Box>

      {/* Department Information */}
      <Box display="flex" flexWrap="wrap" gap={3} mb={3}>
        <Box>
          <Typography variant="subtitle2" color="text.secondary">Department Type</Typography>
          <Typography variant="body1" sx={{ textTransform: 'capitalize' }}>
            {node.department_type || 'Operational'}
          </Typography>
        </Box>
        
        {node.location && (
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Location</Typography>
            <Typography variant="body1" display="flex" alignItems="center">
              <LocationIcon fontSize="small" sx={{ mr: 0.5 }} />
              {node.location}
            </Typography>
          </Box>
        )}
        
        <Box>
          <Typography variant="subtitle2" color="text.secondary">Hierarchy Level</Typography>
          <Typography variant="body1">Level {node.hierarchy_level}</Typography>
        </Box>
        
        <Box>
          <Typography variant="subtitle2" color="text.secondary">Direct Users</Typography>
          <Typography variant="body1" display="flex" alignItems="center">
            <GroupIcon fontSize="small" sx={{ mr: 0.5 }} />
            {node.user_count}
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="subtitle2" color="text.secondary">Child Departments</Typography>
          <Typography variant="body1">{node.children.length}</Typography>
        </Box>
      </Box>

      {/* Department Head */}
      {node.department_head && (
        <Box>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Department Head
          </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar 
              src={node.department_head.profile_picture_url}
              sx={{ width: 48, height: 48 }}
            >
              <PersonIcon />
            </Avatar>
            <Box>
              <Typography variant="body1" fontWeight="medium">
                {node.department_head.full_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {node.department_head.job_title}
              </Typography>
            </Box>
          </Box>
        </Box>
      )}

      {/* Children Summary */}
      {node.children.length > 0 && (
        <Box mt={3}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Child Departments ({node.children.length})
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={1}>
            {node.children.map(child => (
              <Chip
                key={child.id}
                label={`${child.name} (${child.user_count})`}
                size="small"
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      )}
    </Box>
  );
};

// Department Form Dialog Component
interface DepartmentFormDialogProps {
  open: boolean;
  title: string;
  formData: DepartmentFormData;
  onFormDataChange: (data: DepartmentFormData) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

const DepartmentFormDialog: React.FC<DepartmentFormDialogProps> = ({
  open,
  title,
  formData,
  onFormDataChange,
  onSubmit,
  onCancel
}) => {
  const handleChange = (field: keyof DepartmentFormData) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    onFormDataChange({
      ...formData,
      [field]: event.target.value
    });
  };

  return (
    <Dialog open={open} onClose={onCancel} maxWidth="md" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Box display="flex" flexDirection="column" gap={2} pt={1}>
          <TextField
            label="Department Name"
            value={formData.name}
            onChange={handleChange('name')}
            required
            fullWidth
          />
          
          <TextField
            label="Department Code"
            value={formData.code}
            onChange={handleChange('code')}
            required
            fullWidth
          />
          
          <TextField
            label="Description"
            value={formData.description}
            onChange={handleChange('description')}
            multiline
            rows={2}
            fullWidth
          />
          
          <FormControl fullWidth>
            <InputLabel>Department Type</InputLabel>
            <Select
              value={formData.department_type}
              onChange={(e) => onFormDataChange({
                ...formData,
                department_type: e.target.value
              })}
            >
              <MenuItem value="operational">Operational</MenuItem>
              <MenuItem value="administrative">Administrative</MenuItem>
              <MenuItem value="quality">Quality</MenuItem>
              <MenuItem value="research">Research</MenuItem>
              <MenuItem value="regulatory">Regulatory</MenuItem>
            </Select>
          </FormControl>
          
          <TextField
            label="Location"
            value={formData.location}
            onChange={handleChange('location')}
            fullWidth
          />
          
          <TextField
            label="Cost Center"
            value={formData.cost_center}
            onChange={handleChange('cost_center')}
            fullWidth
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={onSubmit} variant="contained">
          {title.includes('Create') ? 'Create' : 'Update'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Department Analytics Dialog Component
interface DepartmentAnalyticsDialogProps {
  open: boolean;
  departmentId: number;
  departmentName: string;
  onClose: () => void;
}

const DepartmentAnalyticsDialog: React.FC<DepartmentAnalyticsDialogProps> = ({
  open,
  departmentId,
  departmentName,
  onClose
}) => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && departmentId) {
      setLoading(true);
      fetch(`/api/v1/org/departments/${departmentId}/analytics`)
        .then(response => response.json())
        .then(data => {
          setAnalytics(data);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [open, departmentId]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>Analytics: {departmentName}</DialogTitle>
      <DialogContent>
        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : analytics ? (
          <Box display="flex" flexDirection="column" gap={3}>
            {/* Key Metrics */}
            <Box display="flex" gap={3}>
              <Box flex={1} textAlign="center" p={2} border="1px solid #e0e0e0" borderRadius={1}>
                <Typography variant="h4" color="primary">{analytics.direct_users}</Typography>
                <Typography variant="body2">Direct Users</Typography>
              </Box>
              <Box flex={1} textAlign="center" p={2} border="1px solid #e0e0e0" borderRadius={1}>
                <Typography variant="h4" color="primary">{analytics.total_users}</Typography>
                <Typography variant="body2">Total Users</Typography>
              </Box>
              <Box flex={1} textAlign="center" p={2} border="1px solid #e0e0e0" borderRadius={1}>
                <Typography variant="h4" color="primary">{analytics.recent_logins_30d}</Typography>
                <Typography variant="body2">Logins (30d)</Typography>
              </Box>
              <Box flex={1} textAlign="center" p={2} border="1px solid #e0e0e0" borderRadius={1}>
                <Typography variant="h4" color="primary">{analytics.child_departments}</Typography>
                <Typography variant="body2">Child Departments</Typography>
              </Box>
            </Box>

            {/* Role Distribution */}
            {Object.keys(analytics.role_distribution || {}).length > 0 && (
              <Box>
                <Typography variant="h6" gutterBottom>Role Distribution</Typography>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {Object.entries(analytics.role_distribution).map(([role, count]) => (
                    <Chip
                      key={role}
                      label={`${role}: ${count}`}
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>
            )}

            {/* Department Head */}
            {analytics.department_head && (
              <Box>
                <Typography variant="h6" gutterBottom>Department Head</Typography>
                <Box display="flex" alignItems="center" gap={2}>
                  <Avatar src={analytics.department_head.profile_picture_url}>
                    <PersonIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="body1">{analytics.department_head.full_name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {analytics.department_head.job_title}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            )}
          </Box>
        ) : (
          <Typography>No analytics data available</Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default DepartmentHierarchy;