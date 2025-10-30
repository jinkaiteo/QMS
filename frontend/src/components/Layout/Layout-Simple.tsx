import React from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  School as TrainingIcon,
  ExitToApp as LogoutIcon,
  Person as PersonIcon,
} from '@mui/icons-material'
import { RootState } from '../../store/store-simple'
import { logoutUser } from '../../store/slices/authSlice-simple'
import { AppDispatch } from '../../store/store-simple'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user } = useSelector((state: RootState) => state.auth)
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null)
  const [drawerOpen, setDrawerOpen] = React.useState(false)

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleProfileMenuClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = async () => {
    await dispatch(logoutUser())
    navigate('/login')
  }

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'Training', icon: <TrainingIcon />, path: '/training' },
  ]

  const drawer = (
    <Box sx={{ width: 250 }}>
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" color="primary">
          QMS Platform
        </Typography>
      </Box>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem
            button
            key={item.text}
            onClick={() => {
              navigate(item.path)
              setDrawerOpen(false)
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={() => setDrawerOpen(true)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            QMS Platform v3.0
          </Typography>

          {user && (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Typography variant="body2" sx={{ mr: 2 }}>
                {user.first_name || user.username}
              </Typography>
              <IconButton
                size="large"
                edge="end"
                aria-label="account of current user"
                aria-controls="profile-menu"
                aria-haspopup="true"
                onClick={handleProfileMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32 }}>
                  <PersonIcon />
                </Avatar>
              </IconButton>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        {drawer}
      </Drawer>

      {/* Profile Menu */}
      <Menu
        id="profile-menu"
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        keepMounted
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        open={Boolean(anchorEl)}
        onClose={handleProfileMenuClose}
      >
        <MenuItem onClick={handleProfileMenuClose}>
          <PersonIcon sx={{ mr: 1 }} />
          Profile
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <LogoutIcon sx={{ mr: 1 }} />
          Logout
        </MenuItem>
      </Menu>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          minHeight: 'calc(100vh - 64px)',
        }}
      >
        {children}
      </Box>
    </Box>
  )
}

export default Layout