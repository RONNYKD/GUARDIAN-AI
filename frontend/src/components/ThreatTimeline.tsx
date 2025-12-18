import { useEffect, useState } from 'react'
import { Shield, AlertTriangle, Info } from 'lucide-react'
import { apiService, Threat } from '@/services/api'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

const severityConfig = {
  critical: { color: 'text-danger-600 dark:text-danger-400', bg: 'bg-danger-100 dark:bg-danger-900/20', icon: AlertTriangle },
  high: { color: 'text-warning-600 dark:text-warning-400', bg: 'bg-warning-100 dark:bg-warning-900/20', icon: AlertTriangle },
  medium: { color: 'text-warning-600 dark:text-warning-400', bg: 'bg-warning-100 dark:bg-warning-900/20', icon: Info },
  low: { color: 'text-gray-600 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-800', icon: Info },
}

export default function ThreatTimeline() {
  const [threats, setThreats] = useState<Threat[]>([])
  const { subscribe } = useWebSocket()

  useEffect(() => {
    loadThreats()

    const unsubscribe = subscribe('threat_detected', (newThreat) => {
      setThreats(prev => [newThreat, ...prev.slice(0, 9)])
    })

    return () => unsubscribe()
  }, [subscribe])

  const loadThreats = async () => {
    try {
      const data = await apiService.getThreats(10)
      setThreats(data)
    } catch (error) {
      console.error('Error loading threats:', error)
      // Mock data for demo
      setThreats([])
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Threats</h3>
        <Shield className="h-5 w-5 text-gray-400" />
      </div>
      
      {threats.length === 0 ? (
        <div className="text-center py-12">
          <Shield className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">No threats detected</p>
        </div>
      ) : (
        <div className="flow-root">
          <ul role="list" className="-mb-8">
            {threats.map((threat, idx) => {
              const config = severityConfig[threat.severity as keyof typeof severityConfig] || severityConfig.low
              const Icon = config.icon

              return (
                <li key={threat.id}>
                  <div className="relative pb-8">
                    {idx !== threats.length - 1 && (
                      <span
                        className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200 dark:bg-gray-700"
                        aria-hidden="true"
                      />
                    )}
                    <div className="relative flex space-x-3">
                      <div>
                        <span className={clsx(
                          'h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white dark:ring-gray-800',
                          config.bg
                        )}>
                          <Icon className={clsx('h-4 w-4', config.color)} />
                        </span>
                      </div>
                      <div className="flex min-w-0 flex-1 justify-between space-x-4">
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {threat.type}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                            {threat.description}
                          </p>
                          <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                            Confidence: {Math.round(threat.confidence * 100)}%
                          </p>
                        </div>
                        <div className="whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-500">
                          <time dateTime={threat.detected_at}>
                            {formatDistanceToNow(new Date(threat.detected_at), { addSuffix: true })}
                          </time>
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
