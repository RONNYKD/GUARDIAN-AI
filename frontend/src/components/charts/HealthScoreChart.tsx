import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { apiService } from '@/services/api'
import { useWebSocket } from '@/contexts/WebSocketContext'

interface HealthDataPoint {
  timestamp: string
  score: number
  security: number
  quality: number
  performance: number
  cost: number
}

export default function HealthScoreChart() {
  const [data, setData] = useState<HealthDataPoint[]>([])
  const { subscribe } = useWebSocket()

  useEffect(() => {
    loadData()

    const unsubscribe = subscribe('health_score', (newData) => {
      setData(prev => [...prev.slice(-50), {
        timestamp: new Date(newData.timestamp).toLocaleTimeString(),
        score: newData.score * 100,
        security: newData.security_score * 100,
        quality: newData.quality_score * 100,
        performance: newData.performance_score * 100,
        cost: newData.cost_score * 100,
      }])
    })

    return () => unsubscribe()
  }, [subscribe])

  const loadData = async () => {
    try {
      const telemetry = await apiService.getTelemetry(50)
      const healthData: HealthDataPoint[] = telemetry.map(record => ({
        timestamp: new Date(record.timestamp).toLocaleTimeString(),
        score: record.quality_score * 100,
        security: 85,
        quality: record.quality_score * 100,
        performance: Math.max(0, 100 - (record.latency_ms / 50)),
        cost: Math.max(0, 100 - (record.cost_usd * 1000)),
      }))
      setData(healthData)
    } catch (error) {
      console.error('Error loading health data:', error)
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Health Score Trend</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
          <XAxis 
            dataKey="timestamp" 
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
          />
          <YAxis 
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            domain={[0, 100]}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
              color: '#F9FAFB'
            }}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="score" 
            stroke="#0ea5e9" 
            strokeWidth={2}
            name="Overall"
            dot={false}
          />
          <Line 
            type="monotone" 
            dataKey="security" 
            stroke="#22c55e" 
            strokeWidth={2}
            name="Security"
            dot={false}
          />
          <Line 
            type="monotone" 
            dataKey="quality" 
            stroke="#f59e0b" 
            strokeWidth={2}
            name="Quality"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
