import React, { useState } from 'react'
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
} from '@mui/material'
import {
  Dashboard,
  Description,
  Science,
  School,
  Assessment,
  People,
  Settings,
  ExpandLess,
  ExpandMore,
  Assignment,
  Biotech,
  Quiz,
  Warning,
  AdminPanelSettings,
} from '@mui/icons-material'

interface MenuItem {
  id: string
  label: string
  icon: React.ReactNode
  path?: string
  children?: MenuItem[]
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
    children: [
      { id: 'documents-list', label: 'All Documents', icon: <Assignment />, path: '/documents' },
      { id: 'documents-create', label: 'Create Document', icon: <Description />, path: '/documents/create' },
    ],
  },
  {
    id: 'lims',
    label: 'Laboratory (LIMS)',
    icon: <Science />,
    children: [
      { id: 'lims-samples', label: 'Samples', icon: <Biotech />, path: '/lims/samples' },
      { id: 'lims-tests', label: 'Test Results', icon: <Assessment />, path: '/lims/tests' },
    ],
  },
  {
    id: 'training',
    label: 'Training Management',
    icon: <School />,
    children: [
      { id: 'training-overview', label: 'Training Overview', icon: <School />, path: '/training' },
      { id: 'training-programs', label: 'Programs', icon: <Quiz />, path: '/training/programs' },
    ],
  },
  {
    id: 'quality',
    label: 'Quality Management',
    icon: <Warning />,
    children: [
      { id: 'quality-events', label: 'Quality Events', icon: <Warning />, path: '/quality/events' },
      { id: 'quality-capas', label: 'CAPA Management', icon: <Assessment />, path: '/quality/capas' },
    ],
  },
  {
    id: 'users',
    label: 'User Management',
    icon: <People />,
    path: '/users',
  },
  {
    id: 'settings',
    label: 'System Settings',
    icon: <Settings />,
    path: '/settings',
  },
]

interface SidebarProps {
  open: boolean
  onClose: () => void
  currentPath?: string
}

const Sidebar: React.FC<SidebarProps> = ({ open, onClose, currentPath = '/' }) => {
  const [openItems, setOpenItems] = useState<string[]>(['documents', 'training'])

  const handleItemClick = (item: MenuItem) => {
    if (item.children) {
      // Toggle submenu
      setOpenItems(prev => 
        prev.includes(item.id)
          ? prev.filter(id => id !== item.id)
          : [...prev, item.id]
      )
    } else if (item.path) {
      // Trigger navigation event
      window.dispatchEvent(new CustomEvent('qms-navigate', { detail: { path: item.path } }))
      onClose()
    }
  }

  const isItemActive = (item: MenuItem): boolean => {
    if (item.path) {
      return currentPath === item.path || currentPath.startsWith(item.path + '/')
    }
    return false
  }

  const drawerWidth = 280

  return (
    <Drawer
      variant="temporary"
      open={open}
      onClose={onClose}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          borderRight: 1,
          borderColor: 'divider',
        },
      }}
    >
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
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
              QMS Platform
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Pharmaceutical Quality Management
            </Typography>
          </Box>
        </Box>

        {/* Navigation Menu */}
        <List sx={{ flex: 1, py: 1 }}>
          {menuItems.map((item) => (
            <React.Fragment key={item.id}>
              <ListItem disablePadding>
                <ListItemButton
                  onClick={() => handleItemClick(item)}
                  selected={isItemActive(item)}
                  sx={{
                    minHeight: 48,
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
                      mr: 3,
                      justifyContent: 'center',
                      color: isItemActive(item) ? 'inherit' : 'action.active',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
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
                </ListItemButton>
              </ListItem>

              {/* Submenu items */}
              {item.children && (
                <Collapse in={openItems.includes(item.id)} timeout="auto" unmountOnExit>
                  <List component="div" disablePadding>
                    {item.children.map((child) => (
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
                              minWidth: 0,
                              mr: 2,
                              justifyContent: 'center',
                              color: isItemActive(child) ? 'inherit' : 'action.active',
                            }}
                          >
                            {child.icon}
                          </ListItemIcon>
                          <ListItemText 
                            primary={child.label}
                            primaryTypographyProps={{
                              fontSize: '0.8rem',
                              fontWeight: isItemActive(child) ? 600 : 400,
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
      </Box>
    </Drawer>
  )
}

export default Sidebar