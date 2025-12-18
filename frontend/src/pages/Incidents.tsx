import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle, Clock, XCircle } from 'lucide-react'
import { apiService, Incident } from '@/services/api'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

export default function Incidents() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const { subscribe } = useWebSocket()

  useEffect(() => {
    loadIncidents()

    const unsubscribe = subscribe('incident_created', (newIncident) => {
      setIncidents(prev => [newIncident, ...prev])
    })

    return () => unsubscribe()
  }, [subscribe])

  const loadIncidents = async () => {
    try {
      const data = await apiService.getIncidents()
      setIncidents(data)
    } catch (error) {
      console.error('Error loading incidents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRemediate = async (id: string) => {
    try {
      const result = await apiService.autoRemediate(id)
      if (result.success) {
        setIncidents(prev => prev.map(inc => 
          inc.id === id ? { ...inc, status: 'resolved', auto_remediated: true } : inc
        ))
      }
    } catch (error) {
      console.error('Error remediating incident:', error)
    }
  }

  const filteredIncidents = selectedStatus === 'all' 
    ? incidents 
    : incidents.filter(inc => inc.status === selectedStatus)

  const statusConfig = {
    open: { color: 'text-danger-600 dark:text-danger-400', bg: 'bg-danger-100 dark:bg-danger-900/20', icon: AlertTriangle },
    investigating: { color: 'text-warning-600 dark:text-warning-400', bg: 'bg-warning-100 dark:bg-warning-900/20', icon: Clock },
    resolved: { color: 'text-success-600 dark:text-success-400', bg: 'bg-success-100 dark:bg-success-900/20', icon: CheckCircle },
    closed: { color: 'text-gray-600 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-800', icon: XCircle },
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
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Incidents</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Track and manage security incidents
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        {Object.entries(statusConfig).map(([status, config]) => {
          const Icon = config.icon
          const count = incidents.filter(inc => inc.status === status).length
          return (
            <button
              key={status}
              onClick={() => setSelectedStatus(selectedStatus === status ? 'all' : status)}
              className={clsx(
                'text-left p-4 rounded-lg border transition-all',
                selectedStatus === status || selectedStatus === 'all'
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'
              )}
            >
              <div className="flex items-center gap-3">
                <div className={clsx('p-2 rounded-lg', config.bg)}>
                  <Icon className={clsx('h-5 w-5', config.color)} />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{count}</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 capitalize">{status}</p>
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Incidents List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        {filteredIncidents.length === 0 ? (
          <div className="text-center py-12">
            <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">No incidents found</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredIncidents.map((incident) => {
              const config = statusConfig[incident.status as keyof typeof statusConfig]
              const Icon = config.icon

              return (
                <li key={incident.id} className="p-6">
                  <div className="flex items-start gap-4">
                    <div className={clsx('p-2 rounded-lg flex-shrink-0', config.bg)}>
                      <Icon className={clsx('h-6 w-6', config.color)} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {incident.title}
                        </h3>
                        <div className="flex items-center gap-2">
                          <span className={clsx(
                            'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                            incident.severity === 'critical' && 'bg-danger-100 text-danger-800 dark:bg-danger-900/20 dark:text-danger-400',
                            incident.severity === 'high' && 'bg-warning-100 text-warning-800 dark:bg-warning-900/20 dark:text-warning-400',
                            incident.severity === 'medium' && 'bg-warning-100 text-warning-800 dark:bg-warning-900/20 dark:text-warning-400',
                            incident.severity === 'low' && 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
                          )}>
                            {incident.severity.toUpperCase()}
                          </span>
                          {incident.auto_remediated && (
                            <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-success-100 text-success-800 dark:bg-success-900/20 dark:text-success-400">
                              Auto-Remediated
                            </span>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        {incident.description}
                      </p>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-500">
                          <span>Threats: {incident.threat_ids.length}</span>
                          <span>{formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}</span>
                        </div>
                        {incident.status === 'open' && (
                          <button
                            onClick={() => handleRemediate(incident.id)}
                            className="px-3 py-1 text-xs font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-md transition-colors"
                          >
                            Auto-Remediate
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
