import { useEffect, useState } from 'react'
import { apiService, MetricsSummary } from '@/services/api'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function Analytics() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null)
  const [timeRange, setTimeRange] = useState(24)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
  }, [timeRange])

  const loadMetrics = async () => {
    setLoading(true)
    try {
      const data = await apiService.getMetrics(timeRange)
      setMetrics(data)
    } catch (error) {
      console.error('Error loading metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  // Mock data for charts
  const costTrendData = [
    { time: '00:00', cost: 0.012 },
    { time: '04:00', cost: 0.015 },
    { time: '08:00', cost: 0.028 },
    { time: '12:00', cost: 0.042 },
    { time: '16:00', cost: 0.038 },
    { time: '20:00', cost: 0.025 },
  ]

  const threatDistribution = [
    { name: 'Prompt Injection', value: 45, color: '#ef4444' },
    { name: 'PII Detected', value: 30, color: '#f59e0b' },
    { name: 'Jailbreak Attempt', value: 15, color: '#f59e0b' },
    { name: 'Toxic Content', value: 10, color: '#f59e0b' },
  ]

  const modelUsage = [
    { model: 'gemini-pro', requests: 1250, cost: 0.145 },
    { model: 'gemini-pro-vision', requests: 320, cost: 0.089 },
    { model: 'text-bison', requests: 180, cost: 0.032 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analytics</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Deep dive into your LLM usage patterns
          </p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
        >
          <option value={1}>Last Hour</option>
          <option value={24}>Last 24 Hours</option>
          <option value={168}>Last Week</option>
          <option value={720}>Last Month</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400">Total Requests</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {metrics?.total_requests.toLocaleString()}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400">Total Cost</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            ${metrics?.total_cost.toFixed(2)}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400">Avg Quality</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {metrics ? `${Math.round(metrics.avg_quality * 100)}%` : '--'}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400">Threat Rate</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {metrics ? `${((metrics.threat_count / metrics.total_requests) * 100).toFixed(2)}%` : '--'}
          </p>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Cost Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={costTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
              <XAxis dataKey="time" stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
              <YAxis stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} tickFormatter={(v) => `$${v}`} />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '0.5rem',
                }}
              />
              <Line type="monotone" dataKey="cost" stroke="#0ea5e9" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Threat Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={threatDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {threatDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '0.5rem',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Model Usage Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Model Usage</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={modelUsage}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
            <XAxis dataKey="model" stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
            <YAxis yAxisId="left" stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
            <YAxis yAxisId="right" orientation="right" stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} tickFormatter={(v) => `$${v}`} />
            <Tooltip 
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '0.5rem',
              }}
            />
            <Legend />
            <Bar yAxisId="left" dataKey="requests" fill="#0ea5e9" name="Requests" />
            <Bar yAxisId="right" dataKey="cost" fill="#f59e0b" name="Cost ($)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
