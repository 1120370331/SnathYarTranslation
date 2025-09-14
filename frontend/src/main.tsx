/**
 * Main Entry Point for Shathyar Translation Frontend
 * 
 * React application with mystical theming and translation functionality
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import App from './App'
import './styles/mystical-theme.css'
import './index.css'

// Create React Query client with mystical configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime in v4)
      retry: (failureCount, error: any) => {
        // Custom retry logic for mystical errors
        if (error?.status === 429) {
          return false; // Don't retry rate limited requests
        }
        if (error?.status >= 500) {
          return failureCount < 2; // Retry server errors up to 2 times
        }
        return failureCount < 1; // Retry other errors once
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: false, // Don't retry mutations by default
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>,
)
