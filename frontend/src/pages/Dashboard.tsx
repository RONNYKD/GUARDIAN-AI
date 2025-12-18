import { useEffect, useState } from 'react'
import { 
  TrendingUp, 
  AlertCircle, 
  Activity, 
  DollarSign,
  Shield,
  Clock,
  Zap,
  Target
} from 'lucide-react'
import { apiService, HealthScore, MetricsSummary } from '@/services/api'
import { useWebSocket } from '@/contexts/WebSocketContext'
import StatCard from '@/components/StatCard'
import HealthScoreChart from '@/components/charts/HealthScoreChart'
import ThreatTimeline from '@/components/ThreatTimeline'
import CostChart from '@/components/charts/CostChart'
import LatencyChart from '@/components/charts/LatencyChart'

export default function Dashboard() {
  const [healthScore, setHealthScore] = useState<HealthScore | null>(null)
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const { subscribe } = useWebSocket()

  useEffect(() => {
    loadData()

    // Subscribe to real-time updates
    const unsubscribeHealth = subscribe('health_score', (data) => {
      setHealthScore(data)
    })

    const unsubscribeMetrics = subscribe('metrics_update', (data) => {
      setMetrics(data)
    })

    return () => {
      unsubscribeHealth()
      unsubscribeMetrics()
    }
  }, [subscribe])

  const loadData = async () => {
    try {
      const [health, metricsData] = await Promise.all([
        apiService.getHealthScore(),
        apiService.getMetrics(24),
      ])
      setHealthScore(health)
      setMetrics(metricsData)
    } catch (error) {
      console.error('Error loading dashboard data:', error)
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Real-time LLM security monitoring and analytics
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Health Score"
          value={healthScore ? `${Math.round(healthScore.score * 100)}%` : '--'}
          icon={Target}
          trend={healthScore && healthScore.score >= 0.8 ? 'up' : 'down'}
          trendValue={healthScore ? `${Math.round((healthScore.score - 0.75) * 100)}%` : ''}
          color="primary"
        />
        <StatCard
          title="Total Requests"
          value={metrics ? metrics.total_requests.toLocaleString() : '--'}
          icon={Activity}
          trend="up"
          trendValue={metrics ? '+12%' : ''}
          color="success"
        />
        <StatCard
          title="Active Threats"
          value={metrics ? metrics.threat_count.toString() : '--'}
          icon={Shield}
          trend={metrics && metrics.threat_count > 0 ? 'down' : 'neutral'}
          trendValue={metrics?.threat_count.toString() || ''}
          color={metrics && metrics.threat_count > 0 ? 'danger' : 'success'}
        />
        <StatCard
          title="Total Cost"
          value={metrics ? `$${metrics.total_cost.toFixed(2)}` : '--'}
          icon={DollarSign}
          trend="up"
          trendValue={metrics ? '+5%' : ''}
          color="warning"
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Avg Latency"
          value={metrics ? `${Math.round(metrics.avg_latency)}ms` : '--'}
          icon={Clock}
          trend={metrics && metrics.avg_latency < 2000 ? 'up' : 'down'}
          color="primary"
          small
        />
        <StatCard
          title="Avg Quality"
          value={healthScore ? `${Math.round(metrics!.avg_quality * 100)}%` : '--'}
          icon={Zap}
          trend="up"
          color="success"
          small
        />
        <StatCard
          title="Incidents"
          value={metrics?.incident_count.toString() || '--'}
          icon={AlertCircle}
          trend="neutral"
          color="danger"
          small
        />
        <StatCard
          title="Error Rate"
          value={metrics ? `${(metrics.error_rate * 100).toFixed(2)}%` : '--'}
          icon={TrendingUp}
          trend={metrics && metrics.error_rate < 0.01 ? 'up' : 'down'}
          color="warning"
          small
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <HealthScoreChart />
        <CostChart />
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LatencyChart />
        <ThreatTimeline />
      </div>
    </div>
  )
}
