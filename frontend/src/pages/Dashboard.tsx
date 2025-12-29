import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  TrendingUp, 
  AlertCircle, 
  Activity, 
  DollarSign,
  Shield,
  Clock,
  Zap,
  Target,
  ArrowUp,
  Minus,
  TrendingDown
} from 'lucide-react'
import { useCountUp } from '../hooks/useCountUp'

const API_BASE = 'http://localhost:8000';

interface MetricsSummary {
  total_requests_24h: number;
  avg_latency_ms: number;
  cost_today_usd: number;
  active_threats: number;
  health_score: number;
  uptime_percentage: number;
  quality_score: number;
  error_rate: number;
}

interface DemoStats {
  total_requests: number;
  threat_count: number;
  threat_breakdown: Record<string, number>;
  avg_quality_score: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  error_count: number;
  error_rate_percent: number;
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [demoStats, setDemoStats] = useState<DemoStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000); // Refresh every 3 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      // Fetch both metrics and demo stats
      const [metricsRes, demoRes] = await Promise.all([
        fetch(`${API_BASE}/api/metrics/summary`).catch(() => null),
        fetch(`${API_BASE}/api/demo/stats`).catch(() => null)
      ]);

      if (metricsRes?.ok) {
        const data = await metricsRes.json();
        setMetrics(data);
      }

      if (demoRes?.ok) {
        const data = await demoRes.json();
        setDemoStats(data);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Combine metrics from both sources (prefer demo stats if available)
  const totalRequests = demoStats?.total_requests || metrics?.total_requests_24h || 0;
  const activeThreats = demoStats?.threat_count || metrics?.active_threats || 0;
  const avgQuality = demoStats?.avg_quality_score || metrics?.quality_score || 0;
  const totalCost = demoStats?.total_cost_usd || metrics?.cost_today_usd || 0;
  const avgLatency = demoStats?.avg_latency_ms || metrics?.avg_latency_ms || 0;
  const errorRate = demoStats ? demoStats.error_rate_percent / 100 : (metrics?.error_rate || 0);
  const healthScore = metrics?.health_score || 95;
  const uptime = metrics?.uptime_percentage || 99.9;

  if (loading) {
    return (
      <div className="space-y-8 animate-in fade-in duration-500">
        {/* Header Skeleton */}
        <div className="space-y-2">
          <div className="h-8 w-48 bg-gray-800 rounded animate-pulse" />
          <div className="h-4 w-96 bg-gray-800 rounded animate-pulse" />
        </div>

        {/* Metrics Skeleton */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-6 shadow-xl animate-pulse">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-12 w-12 bg-gray-700 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 w-24 bg-gray-700 rounded" />
                  <div className="h-6 w-16 bg-gray-700 rounded" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="animate-in slide-in-from-top-4 duration-500">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-400">
          Real-time LLM security monitoring and analytics
        </p>
      </div>

      {/* Primary Metrics */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Health Score"
          value={`${Math.round(healthScore)}%`}
          icon={<Target className="w-6 h-6" />}
          trend={healthScore >= 90 ? 'up' : healthScore >= 70 ? 'neutral' : 'down'}
          trendValue={`${healthScore >= 90 ? '+' : ''}${(healthScore - 85).toFixed(1)}%`}
          color="blue"
        />
        <MetricCard
          title="Total Requests"
          value={totalRequests.toLocaleString()}
          icon={<Activity className="w-6 h-6" />}
          trend="up"
          trendValue="+12.5%"
          color="cyan"
        />
        <MetricCard
          title="Active Threats"
          value={activeThreats.toString()}
          icon={<Shield className="w-6 h-6" />}
          trend={activeThreats > 0 ? 'down' : 'up'}
          trendValue={activeThreats > 0 ? `${activeThreats} detected` : 'All clear'}
          color={activeThreats > 0 ? 'red' : 'emerald'}
        />
        <MetricCard
          title="Total Cost"
          value={`$${totalCost.toFixed(2)}`}
          icon={<DollarSign className="w-6 h-6" />}
          trend="up"
          trendValue="+$5.23"
          color="amber"
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Avg Latency"
          value={`${Math.round(avgLatency)}ms`}
          icon={<Clock className="w-6 h-6" />}
          trend={avgLatency < 1000 ? 'up' : 'down'}
          trendValue={avgLatency < 1000 ? 'Excellent' : 'Needs improvement'}
          color="purple"
        />
        <MetricCard
          title="Avg Quality"
          value={(avgQuality || 0).toFixed(2)}
          icon={<Zap className="w-6 h-6" />}
          trend={avgQuality >= 0.8 ? 'up' : 'down'}
          trendValue={`${avgQuality >= 0.8 ? 'High' : 'Low'} quality`}
          color="blue"
        />
        <MetricCard
          title="Error Rate"
          value={`${(errorRate * 100).toFixed(1)}%`}
          icon={<AlertCircle className="w-6 h-6" />}
          trend={errorRate < 0.05 ? 'up' : 'down'}
          trendValue={errorRate < 0.05 ? 'Low errors' : 'Action needed'}
          color={errorRate < 0.05 ? 'emerald' : 'red'}
        />
        <MetricCard
          title="Uptime"
          value={`${uptime.toFixed(1)}%`}
          icon={<TrendingUp className="w-6 h-6" />}
          trend="up"
          trendValue="99.9% target"
          color="emerald"
        />
      </div>

      {/* Threat Breakdown */}
      {demoStats && demoStats.threat_count > 0 && (
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold text-white mb-6">Threat Breakdown</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {Object.entries(demoStats.threat_breakdown).map(([type, count]) => (
              <div key={type} className="bg-gray-950/50 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors">
                <div className="text-2xl mb-2">{getThreatIcon(type)}</div>
                <div className="text-2xl font-bold font-mono text-white">{count}</div>
                <div className="text-xs text-gray-400 mt-1 capitalize">{type.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* System Health Panel */}
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-6 shadow-xl">
        <h2 className="text-xl font-semibold text-white mb-6">System Health</h2>
        <div className="space-y-4">
          <HealthBar label="Uptime" percentage={uptime} color="emerald" />
          <HealthBar label="Quality" percentage={avgQuality * 100} color="blue" />
          <HealthBar label="Security" percentage={activeThreats === 0 ? 100 : Math.max(0, 100 - activeThreats * 10)} color={activeThreats === 0 ? 'emerald' : 'red'} />
          <HealthBar label="Cost Efficiency" percentage={totalCost < 100 ? 90 : totalCost < 500 ? 60 : 30} color="amber" />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link 
          to="/demo" 
          className="bg-gradient-to-br from-blue-900/30 to-blue-800/30 border border-blue-500/30 rounded-xl p-6 hover:border-blue-500/50 hover:scale-105 transition-all duration-200 group"
        >
          <Target className="w-8 h-8 text-blue-400 mb-4 group-hover:scale-110 transition-transform" />
          <h3 className="text-lg font-semibold text-white mb-2">Launch Demo</h3>
          <p className="text-sm text-gray-400">Test with simulated attacks</p>
        </Link>
        <Link 
          to="/threats" 
          className="bg-gradient-to-br from-red-900/30 to-red-800/30 border border-red-500/30 rounded-xl p-6 hover:border-red-500/50 hover:scale-105 transition-all duration-200 group"
        >
          <Shield className="w-8 h-8 text-red-400 mb-4 group-hover:scale-110 transition-transform" />
          <h3 className="text-lg font-semibold text-white mb-2">View Threats</h3>
          <p className="text-sm text-gray-400">Security threat timeline</p>
        </Link>
        <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/30 border border-purple-500/30 rounded-xl p-6 hover:border-purple-500/50 hover:scale-105 transition-all duration-200 group">
          <Activity className="w-8 h-8 text-purple-400 mb-4 group-hover:scale-110 transition-transform" />
          <h3 className="text-lg font-semibold text-white mb-2">Analytics</h3>
          <p className="text-sm text-gray-400">Deep-dive metrics (coming soon)</p>
        </div>
      </div>
    </div>
  )
}

// Enterprise-grade Metric Card Component
interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend: 'up' | 'down' | 'neutral';
  trendValue: string;
  color: 'blue' | 'cyan' | 'emerald' | 'red' | 'amber' | 'purple';
}

function MetricCard({ title, value, icon, trend, trendValue, color }: MetricCardProps) {
  // Extract numeric value for counter animation
  const numericValue = parseFloat(value.replace(/[^0-9.]/g, '')) || 0;
  const prefix = value.match(/^\$/)?.[0] || '';
  const suffix = value.match(/[a-z%]+$/i)?.[0] || '';
  
  const animatedValue = useCountUp(numericValue, 1500, suffix.includes('%') ? 1 : value.includes('.') ? 2 : 0);

  const colorClasses = {
    blue: 'from-blue-500/10 to-blue-600/10 border-blue-500/20 text-blue-400',
    cyan: 'from-cyan-500/10 to-cyan-600/10 border-cyan-500/20 text-cyan-400',
    emerald: 'from-emerald-500/10 to-emerald-600/10 border-emerald-500/20 text-emerald-400',
    red: 'from-red-500/10 to-red-600/10 border-red-500/20 text-red-400',
    amber: 'from-amber-500/10 to-amber-600/10 border-amber-500/20 text-amber-400',
    purple: 'from-purple-500/10 to-purple-600/10 border-purple-500/20 text-purple-400',
  };

  const iconBg = {
    blue: 'bg-blue-500/10',
    cyan: 'bg-cyan-500/10',
    emerald: 'bg-emerald-500/10',
    red: 'bg-red-500/10',
    amber: 'bg-amber-500/10',
    purple: 'bg-purple-500/10',
  };

  const trendColors = {
    up: 'text-emerald-400',
    down: 'text-red-400',
    neutral: 'text-gray-400',
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} from-gray-900 to-gray-800 border rounded-xl p-6 shadow-xl hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 animate-in fade-in slide-in-from-bottom-4`}>
      {/* Icon */}
      <div className={`${iconBg[color]} rounded-lg p-3 w-fit mb-4 transition-transform hover:scale-110 duration-200`}>
        <div className={colorClasses[color].split(' ')[2]}>
          {icon}
        </div>
      </div>

      {/* Label */}
      <div className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-2">
        {title}
      </div>

      {/* Value with counter animation */}
      <div className="text-4xl font-bold font-mono text-white mb-3">
        {prefix}{animatedValue}{suffix}
      </div>

      {/* Trend */}
      <div className="flex items-center gap-2">
        {trend === 'up' && <ArrowUp className={`w-4 h-4 ${trendColors.up} animate-in fade-in duration-300`} />}
        {trend === 'down' && <TrendingDown className={`w-4 h-4 ${trendColors.down} animate-in fade-in duration-300`} />}
        {trend === 'neutral' && <Minus className={`w-4 h-4 ${trendColors.neutral} animate-in fade-in duration-300`} />}
        <span className={`text-sm font-medium ${trendColors[trend]}`}>
          {trendValue}
        </span>
      </div>
    </div>
  );
}

// Health Bar Component
interface HealthBarProps {
  label: string;
  percentage: number;
  color: 'emerald' | 'blue' | 'red' | 'amber';
}

function HealthBar({ label, percentage, color }: HealthBarProps) {
  const barColors = {
    emerald: 'bg-emerald-500',
    blue: 'bg-blue-500',
    red: 'bg-red-500',
    amber: 'bg-amber-500',
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-300">{label}</span>
        <span className="text-sm font-mono font-semibold text-white">{percentage.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div 
          className={`h-full ${barColors[color]} transition-all duration-500 ease-out`}
          style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
        />
      </div>
    </div>
  );
}

// Helper function for threat icons
function getThreatIcon(type: string): string {
  const icons: Record<string, string> = {
    prompt_injection: '⚠️',
    pii_leak: '🔓',
    jailbreak_attempt: '🚨',
    toxic_content: '☢️',
    cost_spike: '💰',
    quality_degradation: '📉',
  };
  return icons[type] || '⚠️';
}

