import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { WebSocketProvider } from '@/contexts/WebSocketContext'
import ErrorBoundary from '@/components/ErrorBoundary'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import Threats from '@/pages/Threats'
import Incidents from '@/pages/Incidents'
import Traces from '@/pages/Traces'
import Analytics from '@/pages/Analytics'
import Settings from '@/pages/Settings'

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <WebSocketProvider>
          <Router>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="threats" element={<Threats />} />
                <Route path="incidents" element={<Incidents />} />
                <Route path="traces" element={<Traces />} />
                <Route path="analytics" element={<Analytics />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Routes>
          </Router>
        </WebSocketProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}

export default App
