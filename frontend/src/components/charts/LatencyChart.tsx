import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { apiService } from '@/services/api'
import { useWebSocket } from '@/contexts/WebSocketContext'

interface LatencyDataPoint {
  timestamp: string
  latency: number
  p95: number
}

export default function LatencyChart() {
  const [data, setData] = useState<LatencyDataPoint[]>([])
  const { subscribe } = useWebSocket()

  useEffect(() => {
    loadData()

    const unsubscribe = subscribe('telemetry', (newData) => {
      setData(prev => [...prev.slice(-20), {
        timestamp: new Date(newData.timestamp).toLocaleTimeString(),
        latency: newData.latency_ms,
        p95: 5000, // Threshold
      }])
    })

    return () => unsubscribe()
  }, [subscribe])

  const loadData = async () => {
    try {
      const telemetry = await apiService.getTelemetry(20)
      const latencyData: LatencyDataPoint[] = telemetry.map(record => ({
        timestamp: new Date(record.timestamp).toLocaleTimeString(),
        latency: record.latency_ms,
        p95: 5000,
      }))
      setData(latencyData)
    } catch (error) {
      console.error('Error loading latency data:', error)
    }
  }

  const avgLatency = data.length > 0 
    ? data.reduce((sum, d) => sum + d.latency, 0) / data.length 
    : 0

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Latency Distribution</h3>
        <div className="text-right">
          <p className="text-sm text-gray-600 dark:text-gray-400">Average</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{Math.round(avgLatency)}ms</p>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
          <XAxis 
            dataKey="timestamp" 
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
          />
          <YAxis 
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            tickFormatter={(value) => `${value}ms`}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
              color: '#F9FAFB'
            }}
            formatter={(value: number) => [`${value}ms`, 'Latency']}
          />
          <Bar dataKey="latency" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
