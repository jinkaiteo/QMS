import React, { useEffect } from 'react'
import { Snackbar, Alert, IconButton, Box } from '@mui/material'
import { Close } from '@mui/icons-material'
import { useSelector, useDispatch } from 'react-redux'

import { RootState } from '@store/store'
import { removeNotification } from '@store/slices/uiSlice'

const NotificationContainer: React.FC = () => {
  const dispatch = useDispatch()
  const { notifications } = useSelector((state: RootState) => state.ui)

  useEffect(() => {
    // Auto-remove notifications that should auto-hide
    notifications?.forEach((notification) => {
      if (notification.autoHide) {
        const timeout = setTimeout(() => {
          dispatch(removeNotification(notification.id))
        }, notification.duration || 5000)

        return () => clearTimeout(timeout)
      }
    })
  }, [notifications, dispatch])

  const handleClose = (notificationId: string) => {
    dispatch(removeNotification(notificationId))
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 80, // Below header
        right: 16,
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        maxWidth: 400,
      }}
    >
      {notifications?.map((notification) => (
        <Snackbar
          key={notification.id}
          open={true}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ position: 'relative', transform: 'none' }}
        >
          <Alert
            severity={notification.type}
            variant="filled"
            action={
              <IconButton
                size="small"
                aria-label="close"
                color="inherit"
                onClick={() => handleClose(notification.id)}
              >
                <Close fontSize="small" />
              </IconButton>
            }
            sx={{
              width: '100%',
              boxShadow: 2,
            }}
          >
            <Box>
              <Box sx={{ fontWeight: 600, mb: notification.message ? 0.5 : 0 }}>
                {notification.title}
              </Box>
              {notification.message && (
                <Box sx={{ fontSize: '0.875rem', opacity: 0.9 }}>
                  {notification.message}
                </Box>
              )}
            </Box>
          </Alert>
        </Snackbar>
      ))}
    </Box>
  )
}

export default NotificationContainer