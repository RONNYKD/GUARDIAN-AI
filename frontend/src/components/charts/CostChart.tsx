import { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { apiService } from '@/services/api'
import { useWebSocket } from '@/contexts/WebSocketContext'

interface CostDataPoint {
  timestamp: string
  cost: number
  cumulative: number
}

export default function CostChart() {
  const [data, setData] = useState<CostDataPoint[]>([])
  const { subscribe } = useWebSocket()

  useEffect(() => {
    loadData()

    const unsubscribe = subscribe('telemetry', (newData) => {
      setData(prev => {
        const lastCumulative = prev.length > 0 ? prev[prev.length - 1].cumulative : 0
        return [...prev.slice(-50), {
          timestamp: new Date(newData.timestamp).toLocaleTimeString(),
          cost: newData.cost_usd,
          cumulative: lastCumulative + newData.cost_usd,
        }]
      })
    })

    return () => unsubscribe()
  }, [subscribe])

  const loadData = async () => {
    try {
      const telemetry = await apiService.getTelemetry(50)
      let cumulative = 0
      const costData: CostDataPoint[] = telemetry.map(record => {
        cumulative += record.cost_usd
        return {
          timestamp: new Date(record.timestamp).toLocaleTimeString(),
          cost: record.cost_usd,
          cumulative,
        }
      })
      setData(costData)
    } catch (error) {
      console.error('Error loading cost data:', error)
    }
  }

  const totalCost = data.length > 0 ? data[data.length - 1].cumulative : 0

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Cost Analytics</h3>
        <div className="text-right">
          <p className="text-sm text-gray-600 dark:text-gray-400">Total Cost</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">${totalCost.toFixed(4)}</p>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
          <XAxis 
            dataKey="timestamp" 
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
          />
          <YAxis 
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            tickFormatter={(value) => `$${value.toFixed(4)}`}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
              color: '#F9FAFB'
            }}
            formatter={(value: number) => [`$${value.toFixed(6)}`, 'Cost']}
          />
          <Area 
            type="monotone" 
            dataKey="cumulative" 
            stroke="#f59e0b" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorCost)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
