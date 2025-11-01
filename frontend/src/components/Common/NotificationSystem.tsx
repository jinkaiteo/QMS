import React, { useState, useEffect, createContext, useContext } from 'react'
import {
  Snackbar,
  Alert,
  AlertTitle,
  IconButton,
  Badge,
  Menu,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Typography,
  Box,
  Divider,
  Button,
  Chip,
} from '@mui/material'
import {
  Close,
  Notifications,
  NotificationsActive,
  Warning,
  Info,
  CheckCircle,
  Error,
  Assignment,
  Science,
  Description,
  School,
} from '@mui/icons-material'

// Notification types
interface Notification {
  id: string
  title: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  module?: 'documents' | 'training' | 'quality' | 'lims' | 'system'
  timestamp: Date
  read: boolean
  actionUrl?: string
  priority: 'low' | 'medium' | 'high'
}

interface ToastNotification {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
}

// Context for notifications
interface NotificationContextType {
  notifications: Notification[]
  unreadCount: number
  showToast: (message: string, type: 'success' | 'error' | 'warning' | 'info', duration?: number) => void
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  removeNotification: (id: string) => void
}

const NotificationContext = createContext<NotificationContextType | null>(null)

// Custom hook to use notifications
export const useNotifications = () => {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider')
  }
  return context
}

// Toast notification component
const ToastNotification: React.FC<{
  notification: ToastNotification
  onClose: () => void
}> = ({ notification, onClose }) => {
  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle />
      case 'error':
        return <Error />
      case 'warning':
        return <Warning />
      default:
        return <Info />
    }
  }

  return (
    <Snackbar
      open={true}
      autoHideDuration={notification.duration || 6000}
      onClose={onClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
    >
      <Alert
        severity={notification.type}
        onClose={onClose}
        icon={getIcon(notification.type)}
        sx={{ minWidth: 300 }}
      >
        {notification.message}
      </Alert>
    </Snackbar>
  )
}

// Notification bell component
export const NotificationBell: React.FC = () => {
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const open = Boolean(anchorEl)

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const getModuleIcon = (module?: string) => {
    switch (module) {
      case 'documents':
        return <Description fontSize="small" />
      case 'training':
        return <School fontSize="small" />
      case 'quality':
        return <Warning fontSize="small" />
      case 'lims':
        return <Science fontSize="small" />
      default:
        return <Assignment fontSize="small" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error'
      case 'medium':
        return 'warning'
      default:
        return 'default'
    }
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  return (
    <>
      <IconButton
        color="inherit"
        onClick={handleClick}
        sx={{ ml: 1 }}
      >
        <Badge badgeContent={unreadCount} color="error">
          {unreadCount > 0 ? <NotificationsActive /> : <Notifications />}
        </Badge>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 400,
            maxHeight: 500,
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, pb: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Notifications</Typography>
            {unreadCount > 0 && (
              <Button size="small" onClick={markAllAsRead}>
                Mark all read
              </Button>
            )}
          </Box>
        </Box>

        <Divider />

        {notifications.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="textSecondary">No notifications</Typography>
          </Box>
        ) : (
          <List sx={{ maxHeight: 300, overflow: 'auto' }}>
            {notifications.slice(0, 10).map((notification) => (
              <ListItem
                key={notification.id}
                button
                onClick={() => {
                  markAsRead(notification.id)
                  if (notification.actionUrl) {
                    // Handle navigation to notification action
                    window.dispatchEvent(new CustomEvent('qms-navigate', {
                      detail: { path: notification.actionUrl }
                    }))
                  }
                  handleClose()
                }}
                sx={{
                  backgroundColor: notification.read ? 'transparent' : 'action.hover',
                  '&:hover': {
                    backgroundColor: 'action.selected',
                  },
                }}
              >
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: notification.read ? 'grey.300' : 'primary.main' }}>
                    {getModuleIcon(notification.module)}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: notification.read ? 400 : 600 }}>
                        {notification.title}
                      </Typography>
                      <Chip
                        label={notification.priority}
                        size="small"
                        color={getPriorityColor(notification.priority) as any}
                        variant="outlined"
                        sx={{ height: 16, fontSize: '0.65rem' }}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 0.5 }}>
                        {notification.message}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {formatTime(notification.timestamp)}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}

        {notifications.length > 10 && (
          <>
            <Divider />
            <Box sx={{ p: 1, textAlign: 'center' }}>
              <Button size="small" fullWidth>
                View all notifications
              </Button>
            </Box>
          </>
        )}
      </Menu>
    </>
  )
}

// Notification provider component
export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [toasts, setToasts] = useState<ToastNotification[]>([])

  // Mock notifications for demo
  useEffect(() => {
    const mockNotifications: Notification[] = [
      {
        id: '1',
        title: 'Training Due Soon',
        message: 'GMP Level 1 training is due in 3 days for John Doe',
        type: 'warning',
        module: 'training',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        read: false,
        priority: 'high',
        actionUrl: '/training'
      },
      {
        id: '2',
        title: 'Document Approved',
        message: 'SOP-001 "Batch Record Review" has been approved',
        type: 'success',
        module: 'documents',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
        read: false,
        priority: 'medium',
        actionUrl: '/documents'
      },
      {
        id: '3',
        title: 'Quality Event Assigned',
        message: 'Temperature deviation QE-2024-003 has been assigned to you',
        type: 'warning',
        module: 'quality',
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
        read: true,
        priority: 'high',
        actionUrl: '/quality'
      },
      {
        id: '4',
        title: 'Sample Test Completed',
        message: 'Test results available for sample S-2024-001',
        type: 'info',
        module: 'lims',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
        read: true,
        priority: 'low',
        actionUrl: '/lims'
      }
    ]

    setNotifications(mockNotifications)
  }, [])

  const unreadCount = notifications.filter(n => !n.read).length

  const showToast = (message: string, type: 'success' | 'error' | 'warning' | 'info', duration = 6000) => {
    const id = Date.now().toString()
    const toast: ToastNotification = { id, message, type, duration }
    setToasts(prev => [...prev, toast])

    // Auto remove toast after duration
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, duration)
  }

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false,
    }
    setNotifications(prev => [newNotification, ...prev])
  }

  const markAsRead = (id: string) => {
    setNotifications(prev => prev.map(n => 
      n.id === id ? { ...n, read: true } : n
    ))
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }

  const contextValue: NotificationContextType = {
    notifications,
    unreadCount,
    showToast,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
  }

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
      {/* Render toast notifications */}
      {toasts.map(toast => (
        <ToastNotification
          key={toast.id}
          notification={toast}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </NotificationContext.Provider>
  )
}

export default NotificationProvider