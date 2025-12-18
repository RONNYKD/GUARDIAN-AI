import { useEffect, useState } from 'react'
import { Activity, Search, Filter } from 'lucide-react'
import { apiService, TelemetryRecord } from '@/services/api'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

export default function Traces() {
  const [traces, setTraces] = useState<TelemetryRecord[]>([])
  const [filteredTraces, setFilteredTraces] = useState<TelemetryRecord[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedModel, setSelectedModel] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const { subscribe } = useWebSocket()

  useEffect(() => {
    loadTraces()

    const unsubscribe = subscribe('telemetry', (newTrace) => {
      setTraces(prev => [newTrace, ...prev.slice(0, 99)])
    })

    return () => unsubscribe()
  }, [subscribe])

  useEffect(() => {
    let filtered = traces

    if (selectedModel !== 'all') {
      filtered = filtered.filter(t => t.model === selectedModel)
    }

    if (searchTerm) {
      filtered = filtered.filter(t => 
        t.trace_id.includes(searchTerm) ||
        t.prompt.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.response.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    setFilteredTraces(filtered)
  }, [traces, selectedModel, searchTerm])

  const loadTraces = async () => {
    try {
      const data = await apiService.getTelemetry(100)
      setTraces(data)
    } catch (error) {
      console.error('Error loading traces:', error)
    } finally {
      setLoading(false)
    }
  }

  const uniqueModels = Array.from(new Set(traces.map(t => t.model)))

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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Traces</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          View and analyze LLM request traces
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search traces..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent appearance-none"
            >
              <option value="all">All Models</option>
              {uniqueModels.map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Traces List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        {filteredTraces.length === 0 ? (
          <div className="text-center py-12">
            <Activity className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">No traces found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Trace ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Model
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Tokens
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Latency
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Quality
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredTraces.map((trace) => (
                  <tr key={trace.trace_id} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-white">
                      {trace.trace_id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      {trace.model}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      {trace.input_tokens + trace.output_tokens}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={clsx(
                        trace.latency_ms > 5000 
                          ? 'text-danger-600 dark:text-danger-400' 
                          : 'text-gray-600 dark:text-gray-400'
                      )}>
                        {trace.latency_ms}ms
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      ${trace.cost_usd.toFixed(6)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={clsx(
                        trace.quality_score >= 0.7 
                          ? 'text-success-600 dark:text-success-400' 
                          : 'text-warning-600 dark:text-warning-400'
                      )}>
                        {Math.round(trace.quality_score * 100)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-500">
                      {formatDistanceToNow(new Date(trace.timestamp), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
