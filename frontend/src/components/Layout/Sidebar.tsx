import React from 'react'
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Divider,
  Box,
  Typography,
  useTheme,
  useMediaQuery,
} from '@mui/material'
import {
  Dashboard,
  Description,
  Science,
  School,
  Warning,
  People,
  Settings,
  ExpandLess,
  ExpandMore,
  Assignment,
  BugReport,
  SecurityOutlined,
  AnalyticsOutlined,
} from '@mui/icons-material'
import { useSelector, useDispatch } from 'react-redux'
import { useNavigate, useLocation } from 'react-router-dom'

import { RootState } from '@store/store'
import { setSidebarOpen } from '@store/slices/uiSlice'
import { authService } from '@services/authService'

interface MenuItem {
  id: string
  label: string
  icon: React.ReactNode
  path?: string
  children?: MenuItem[]
  permission?: string
  roles?: string[]
}

const menuItems: MenuItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <Dashboard />,
    path: '/dashboard',
  },
  {
    id: 'documents',
    label: 'Document Management',
    icon: <Description />,
    path: '/documents',
    permission: 'documents.view',
    children: [
      { id: 'documents-list', label: 'All Documents', icon: <Assignment />, path: '/documents' },
      { id: 'documents-create', label: 'Create Document', icon: <Description />, path: '/documents/create', permission: 'documents.create' },
    ],
  },
  {
    id: 'lims',
    label: 'Laboratory (LIMS)',
    icon: <Science />,
    path: '/lims',
    permission: 'lims.view',
    children: [
      { id: 'lims-samples', label: 'Samples', icon: <Science />, path: '/lims/samples' },
      { id: 'lims-tests', label: 'Test Results', icon: <AnalyticsOutlined />, path: '/lims/tests' },
      { id: 'lims-methods', label: 'Test Methods', icon: <Assignment />, path: '/lims/methods' },
    ],
  },
  {
    id: 'training',
    label: 'Training Management',
    icon: <School />,
    path: '/training',
    permission: 'training.view',
    children: [
      { id: 'training-overview', label: 'Training Overview', icon: <School />, path: '/training' },
      { id: 'training-programs', label: 'Training Programs', icon: <Assignment />, path: '/training/programs' },
      { id: 'training-assignments', label: 'Assignments', icon: <SecurityOutlined />, path: '/training/assignments' },
    ],
  },
  {
    id: 'quality',
    label: 'Quality Management',
    icon: <Warning />,
    path: '/quality',
    permission: 'quality.view',
    children: [
      { id: 'quality-events', label: 'Quality Events', icon: <Warning />, path: '/quality/events' },
      { id: 'quality-capas', label: 'CAPA Management', icon: <BugReport />, path: '/quality/capas' },
      { id: 'quality-risks', label: 'Risk Management', icon: <SecurityOutlined />, path: '/quality/risks' },
    ],
  },
  {
    id: 'users',
    label: 'User Management',
    icon: <People />,
    path: '/users',
    permission: 'users.view',
    roles: ['admin', 'manager'],
  },
  {
    id: 'settings',
    label: 'System Settings',
    icon: <Settings />,
    path: '/settings',
    permission: 'settings.view',
    roles: ['admin'],
  },
]

const Sidebar: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useDispatch()
  
  const { user } = useSelector((state: RootState) => state.auth)
  const { sidebarOpen, sidebarCollapsed } = useSelector((state: RootState) => state.ui)
  
  const [openItems, setOpenItems] = React.useState<string[]>([])

  const handleItemClick = (item: MenuItem) => {
    if (item.children) {
      // Toggle submenu
      setOpenItems(prev => 
        prev.includes(item.id)
          ? prev.filter(id => id !== item.id)
          : [...prev, item.id]
      )
    } else if (item.path) {
      // Navigate to path
      navigate(item.path)
      if (isMobile) {
        dispatch(setSidebarOpen(false))
      }
    }
  }

  const isItemVisible = (item: MenuItem): boolean => {
    // For development/testing - show all items for admin users
    if (user?.role === 'admin') {
      return true
    }
    
    // Check permissions for non-admin users
    if (item.permission && !authService.hasPermission(user, item.permission)) {
      return false
    }
    if (item.roles && !authService.hasRole(user, item.roles)) {
      return false
    }
    return true
  }

  const isItemActive = (item: MenuItem): boolean => {
    if (item.path) {
      return location.pathname === item.path || location.pathname.startsWith(item.path + '/')
    }
    return false
  }

  const drawerWidth = sidebarCollapsed ? 72 : 280

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Sidebar Header */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          minHeight: 64,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        {!sidebarCollapsed && (
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
              QMS Platform
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Pharmaceutical Quality Management
            </Typography>
          </Box>
        )}
      </Box>

      {/* Navigation Menu */}
      <List sx={{ flex: 1, py: 1 }}>
        {menuItems.filter(isItemVisible).map((item) => (
          <React.Fragment key={item.id}>
            <ListItem disablePadding>
              <ListItemButton
                onClick={() => handleItemClick(item)}
                selected={isItemActive(item)}
                sx={{
                  minHeight: 48,
                  justifyContent: sidebarCollapsed ? 'center' : 'initial',
                  px: 2.5,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.main',
                    color: 'primary.contrastText',
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                    '&:hover': {
                      backgroundColor: 'primary.dark',
                    },
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: sidebarCollapsed ? 0 : 3,
                    justifyContent: 'center',
                    color: isItemActive(item) ? 'inherit' : 'action.active',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                {!sidebarCollapsed && (
                  <>
                    <ListItemText 
                      primary={item.label}
                      primaryTypographyProps={{
                        fontSize: '0.875rem',
                        fontWeight: isItemActive(item) ? 600 : 400,
                      }}
                    />
                    {item.children && (
                      openItems.includes(item.id) ? <ExpandLess /> : <ExpandMore />
                    )}
                  </>
                )}
              </ListItemButton>
            </ListItem>

            {/* Submenu items */}
            {!sidebarCollapsed && item.children && (
              <Collapse in={openItems.includes(item.id)} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {item.children.filter(isItemVisible).map((child) => (
                    <ListItem key={child.id} disablePadding>
                      <ListItemButton
                        onClick={() => handleItemClick(child)}
                        selected={isItemActive(child)}
                        sx={{
                          pl: 4,
                          minHeight: 40,
                          '&.Mui-selected': {
                            backgroundColor: 'primary.light',
                            color: 'primary.contrastText',
                          },
                        }}
                      >
                        <ListItemIcon
                          sx={{
                            minWidth: 32,
                            color: isItemActive(child) ? 'inherit' : 'action.active',
                          }}
                        >
                          {child.icon}
                        </ListItemIcon>
                        <ListItemText 
                          primary={child.label}
                          primaryTypographyProps={{
                            fontSize: '0.8rem',
                          }}
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            )}
          </React.Fragment>
        ))}
      </List>

      {/* Sidebar Footer */}
      {!sidebarCollapsed && (
        <>
          <Divider />
          <Box sx={{ p: 2 }}>
            <Typography variant="caption" color="textSecondary">
              Version 3.0.0
            </Typography>
            <br />
            <Typography variant="caption" color="textSecondary">
              21 CFR Part 11 Compliant
            </Typography>
          </Box>
        </>
      )}
    </Box>
  )

  return (
    <Drawer
      variant={isMobile ? 'temporary' : 'persistent'}
      open={sidebarOpen}
      onClose={() => dispatch(setSidebarOpen(false))}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          borderRight: 1,
          borderColor: 'divider',
          marginTop: isMobile ? 0 : '64px',
          height: isMobile ? '100%' : 'calc(100% - 64px)',
        },
      }}
      ModalProps={{
        keepMounted: true, // Better open performance on mobile
      }}
    >
      {drawer}
    </Drawer>
  )
}

export default Sidebar