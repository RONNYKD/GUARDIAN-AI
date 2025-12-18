import { useEffect, useState } from 'react'
import { Shield, Search, Filter } from 'lucide-react'
import { apiService, Threat } from '@/services/api'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

export default function Threats() {
  const [threats, setThreats] = useState<Threat[]>([])
  const [filteredThreats, setFilteredThreats] = useState<Threat[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const { subscribe } = useWebSocket()

  useEffect(() => {
    loadThreats()

    const unsubscribe = subscribe('threat_detected', (newThreat) => {
      setThreats(prev => [newThreat, ...prev])
    })

    return () => unsubscribe()
  }, [subscribe])

  useEffect(() => {
    let filtered = threats

    if (selectedSeverity !== 'all') {
      filtered = filtered.filter(t => t.severity === selectedSeverity)
    }

    if (searchTerm) {
      filtered = filtered.filter(t => 
        t.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    setFilteredThreats(filtered)
  }, [threats, selectedSeverity, searchTerm])

  const loadThreats = async () => {
    try {
      const data = await apiService.getThreats(100)
      setThreats(data)
    } catch (error) {
      console.error('Error loading threats:', error)
    } finally {
      setLoading(false)
    }
  }

  const severityColors = {
    critical: 'bg-danger-100 text-danger-800 dark:bg-danger-900/20 dark:text-danger-400',
    high: 'bg-warning-100 text-warning-800 dark:bg-warning-900/20 dark:text-warning-400',
    medium: 'bg-warning-100 text-warning-800 dark:bg-warning-900/20 dark:text-warning-400',
    low: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Threats</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Monitor and investigate security threats
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Shield className="h-8 w-8 text-primary-600 dark:text-primary-400" />
          <div className="text-right">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Threats</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{threats.length}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search threats..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent appearance-none"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Threats List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        {filteredThreats.length === 0 ? (
          <div className="text-center py-12">
            <Shield className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">No threats found</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredThreats.map((threat) => (
              <li key={threat.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <Shield className={clsx(
                      'h-10 w-10',
                      threat.severity === 'critical' && 'text-danger-600 dark:text-danger-400',
                      threat.severity === 'high' && 'text-warning-600 dark:text-warning-400',
                      threat.severity === 'medium' && 'text-warning-600 dark:text-warning-400',
                      threat.severity === 'low' && 'text-gray-600 dark:text-gray-400'
                    )} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {threat.type}
                      </h3>
                      <span className={clsx(
                        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                        severityColors[threat.severity as keyof typeof severityColors]
                      )}>
                        {threat.severity.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      {threat.description}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-500">
                      <span>Trace: {threat.trace_id.substring(0, 8)}</span>
                      <span>Confidence: {Math.round(threat.confidence * 100)}%</span>
                      <span>{formatDistanceToNow(new Date(threat.detected_at), { addSuffix: true })}</span>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
