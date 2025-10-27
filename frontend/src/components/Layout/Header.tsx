import React, { useState } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  ListItemIcon,
  Badge,
  Tooltip,
} from '@mui/material'
import {
  Menu as MenuIcon,
  AccountCircle,
  Settings,
  Logout,
  Notifications,
  Help,
  Security,
} from '@mui/icons-material'
import { useSelector, useDispatch } from 'react-redux'
import { useNavigate } from 'react-router-dom'

import { RootState } from '@store/store'
import { toggleSidebar } from '@store/slices/uiSlice'
import { logoutUser } from '@store/slices/authSlice'
import { authService } from '@services/authService'

const Header: React.FC = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { user } = useSelector((state: RootState) => state.auth)
  const { pageTitle, notifications } = useSelector((state: RootState) => state.ui)
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null)

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleNotificationOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget)
  }

  const handleNotificationClose = () => {
    setNotificationAnchor(null)
  }

  const handleLogout = async () => {
    handleMenuClose()
    await dispatch(logoutUser())
    navigate('/login')
  }

  const handleProfile = () => {
    handleMenuClose()
    navigate('/settings/profile')
  }

  const handleSettings = () => {
    handleMenuClose()
    navigate('/settings')
  }

  const userDisplayName = authService.getUserDisplayName(user)
  const unreadNotifications = notifications?.filter(n => n.type === 'error' || n.type === 'warning').length || 0

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: 'primary.main',
        boxShadow: (theme) => theme.shadows[2],
      }}
    >
      <Toolbar>
        {/* Menu Toggle Button */}
        <IconButton
          color="inherit"
          aria-label="toggle sidebar"
          onClick={() => dispatch(toggleSidebar())}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        {/* Logo and Title */}
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Typography
            variant="h6"
            noWrap
            sx={{
              fontWeight: 600,
              color: 'inherit',
              textDecoration: 'none',
              mr: 2,
            }}
          >
            QMS Platform v3.0
          </Typography>
          
          {pageTitle !== 'QMS Platform' && (
            <>
              <Typography variant="body2" sx={{ opacity: 0.7, mr: 1 }}>
                /
              </Typography>
              <Typography variant="body1" sx={{ opacity: 0.9 }}>
                {pageTitle}
              </Typography>
            </>
          )}
        </Box>

        {/* Right side actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Notifications */}
          <Tooltip title="Notifications">
            <IconButton
              color="inherit"
              onClick={handleNotificationOpen}
            >
              <Badge badgeContent={unreadNotifications} color="error">
                <Notifications />
              </Badge>
            </IconButton>
          </Tooltip>

          {/* Help */}
          <Tooltip title="Help & Documentation">
            <IconButton
              color="inherit"
              onClick={() => window.open('/docs', '_blank')}
            >
              <Help />
            </IconButton>
          </Tooltip>

          {/* User Menu */}
          <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
            <Typography variant="body2" sx={{ mr: 1, display: { xs: 'none', sm: 'block' } }}>
              {userDisplayName}
            </Typography>
            <IconButton
              onClick={handleMenuOpen}
              size="small"
              sx={{ ml: 1 }}
              aria-controls={anchorEl ? 'account-menu' : undefined}
              aria-haspopup="true"
              aria-expanded={anchorEl ? 'true' : undefined}
            >
              <Avatar
                sx={{ 
                  width: 32, 
                  height: 32,
                  backgroundColor: 'secondary.main',
                  fontSize: '0.875rem',
                }}
              >
                {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
              </Avatar>
            </IconButton>
          </Box>
        </Box>

        {/* User Menu Dropdown */}
        <Menu
          anchorEl={anchorEl}
          id="account-menu"
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          onClick={handleMenuClose}
          PaperProps={{
            elevation: 0,
            sx: {
              overflow: 'visible',
              filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
              mt: 1.5,
              minWidth: 200,
              '& .MuiAvatar-root': {
                width: 32,
                height: 32,
                ml: -0.5,
                mr: 1,
              },
            },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItem onClick={handleProfile}>
            <ListItemIcon>
              <AccountCircle fontSize="small" />
            </ListItemIcon>
            Profile
          </MenuItem>
          <MenuItem onClick={handleSettings}>
            <ListItemIcon>
              <Settings fontSize="small" />
            </ListItemIcon>
            Settings
          </MenuItem>
          <Divider />
          <MenuItem onClick={() => navigate('/settings/security')}>
            <ListItemIcon>
              <Security fontSize="small" />
            </ListItemIcon>
            Security
          </MenuItem>
          <MenuItem onClick={handleLogout}>
            <ListItemIcon>
              <Logout fontSize="small" />
            </ListItemIcon>
            Logout
          </MenuItem>
        </Menu>

        {/* Notifications Menu */}
        <Menu
          anchorEl={notificationAnchor}
          open={Boolean(notificationAnchor)}
          onClose={handleNotificationClose}
          PaperProps={{
            sx: { maxWidth: 300, mt: 1.5 }
          }}
        >
          {(notifications?.length || 0) === 0 ? (
            <MenuItem>
              <Typography variant="body2" color="textSecondary">
                No notifications
              </Typography>
            </MenuItem>
          ) : (
            notifications?.slice(0, 5).map((notification) => (
              <MenuItem key={notification.id} onClick={handleNotificationClose}>
                <Box>
                  <Typography variant="subtitle2">
                    {notification.title}
                  </Typography>
                  {notification.message && (
                    <Typography variant="body2" color="textSecondary">
                      {notification.message}
                    </Typography>
                  )}
                </Box>
              </MenuItem>
            ))
          )}
        </Menu>
      </Toolbar>
    </AppBar>
  )
}

export default Header