import React, { useEffect } from 'react'
import { Box, useTheme, useMediaQuery } from '@mui/material'
import { useSelector, useDispatch } from 'react-redux'

import { RootState } from '@store/store'
import { setSidebarOpen } from '@store/slices/uiSlice'
import Header from './Header'
import Sidebar from './Sidebar'
import NotificationContainer from '../Common/NotificationContainer'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const dispatch = useDispatch()
  
  const { sidebarOpen, sidebarCollapsed } = useSelector((state: RootState) => state.ui)

  // Close sidebar on mobile by default
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      dispatch(setSidebarOpen(false))
    }
  }, [isMobile, sidebarOpen, dispatch])

  const sidebarWidth = sidebarCollapsed ? 72 : 280

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Header */}
      <Header />

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          backgroundColor: 'background.default',
          marginTop: '64px', // Header height
          marginLeft: isMobile ? 0 : sidebarOpen ? `${sidebarWidth}px` : 0,
          transition: theme.transitions.create(['margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          minHeight: 'calc(100vh - 64px)',
          overflow: 'auto',
        }}
      >
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      </Box>

      {/* Notification Container */}
      <NotificationContainer />
    </Box>
  )
}

export default Layout