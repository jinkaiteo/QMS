import { configureStore } from '@reduxjs/toolkit'
import { setupListeners } from '@reduxjs/toolkit/query'

import authSlice from './slices/authSlice'
import uiSlice from './slices/uiSlice'
import documentSlice from './slices/documentSlice'
import limsSlice from './slices/limsSlice'
import trainingSlice from './slices/trainingSlice'
import qualitySlice from './slices/qualitySlice'
import userSlice from './slices/userSlice'

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    ui: uiSlice.reducer,
    documents: documentSlice.reducer,
    lims: limsSlice.reducer,
    training: trainingSlice.reducer,
    quality: qualitySlice.reducer,
    users: userSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
})

// Setup listeners for automatic refetching
setupListeners(store.dispatch)

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export default store