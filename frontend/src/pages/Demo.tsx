import { useState, useEffect } from 'react';
import { Rocket, Target, Zap, AlertTriangle, DollarSign, Activity, Trash2 } from 'lucide-react';
import { useCountUp } from '../hooks/useCountUp';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const ATTACK_TYPES = [
  { id: 'normal', name: 'Normal Request', icon: '✓' },
  { id: 'prompt_injection', name: 'Prompt Injection', icon: '⚠️' },
  { id: 'pii_leak', name: 'PII Leak', icon: '🔓' },
  { id: 'jailbreak_attempt', name: 'Jailbreak Attempt', icon: '🚨' },
  { id: 'toxic_content', name: 'Toxic Content', icon: '☢️' },
  { id: 'cost_spike', name: 'Cost Spike', icon: '💰' },
  { id: 'quality_degradation', name: 'Quality Degradation', icon: '📉' },
  { id: 'latency_spike', name: 'Latency Spike', icon: '⏱️' },
  { id: 'error_burst', name: 'Error Burst', icon: '❌' },
];

const SCENARIOS = [
  { id: 'security_breach', name: 'Security Breach', icon: '🛡️', steps: 14, gradient: 'from-red-600/30 to-red-500/30', border: 'border-red-500' },
  { id: 'cost_crisis', name: 'Cost Crisis', icon: '💸', steps: 60, gradient: 'from-yellow-600/30 to-yellow-500/30', border: 'border-yellow-500' },
  { id: 'quality_decline', name: 'Quality Decline', icon: '📊', steps: 20, gradient: 'from-blue-600/30 to-blue-500/30', border: 'border-blue-500' },
  { id: 'system_stress', name: 'System Stress', icon: '⚡', steps: 35, gradient: 'from-purple-600/30 to-purple-500/30', border: 'border-purple-500' },
  { id: 'comprehensive', name: 'Comprehensive', icon: '🎯', steps: 65, gradient: 'from-cyan-600/30 to-cyan-500/30', border: 'border-cyan-500' },
];

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

interface ScenarioStatus {
  scenario_id: string;
  status: 'running' | 'completed' | 'failed';
  progress_percent: number;
  current_step_name: string;
  current_step: number;
  total_steps: number;
  records_created: number;
  elapsed_seconds: number;
}

export default function Demo() {
  const [selectedAttack, setSelectedAttack] = useState('prompt_injection');
  const [attackCount, setAttackCount] = useState(10);
  const [launching, setLaunching] = useState(false);
  const [stats, setStats] = useState<DemoStats | null>(null);
  const [runningScenario, setRunningScenario] = useState<ScenarioStatus | null>(null);
  const [lastMessage, setLastMessage] = useState('');

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (runningScenario?.status === 'running') {
      const interval = setInterval(checkScenarioStatus, 1000);
      return () => clearInterval(interval);
    }
  }, [runningScenario?.scenario_id]);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/demo/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const checkScenarioStatus = async () => {
    if (!runningScenario?.scenario_id) return;
    try {
      const res = await fetch(`${API_BASE}/api/demo/status/${runningScenario.scenario_id}`);
      if (res.ok) {
        const data = await res.json();
        setRunningScenario(data);
        if (data.status === 'completed' || data.status === 'failed') {
          setLastMessage(data.status === 'completed' ? 'Scenario completed successfully!' : 'Scenario failed!');
          setTimeout(() => setRunningScenario(null), 2000);
        }
      }
    } catch (error) {
      console.error('Error checking scenario status:', error);
    }
  };

  const launchAttack = async () => {
    setLaunching(true);
    setLastMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/demo/launch-attack`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attack_type: selectedAttack, count: attackCount }),
      });
      if (res.ok) {
        await res.json();
        setLastMessage(`✅ Launched ${attackCount}x ${selectedAttack} attacks!`);
        setTimeout(() => setLastMessage(''), 3000);
      }
    } catch (error) {
      setLastMessage('❌ Failed to launch attack');
    } finally {
      setLaunching(false);
    }
  };

  const runScenario = async (scenarioType: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/demo/run-scenario`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_type: scenarioType, speed: 'normal' }),
      });
      if (res.ok) {
        const data = await res.json();
        setRunningScenario({ ...data, status: 'running', progress_percent: 0 });
      }
    } catch (error) {
      console.error('Error running scenario:', error);
    }
  };

  const resetDemo = async () => {
    if (!confirm('This will delete all demo data. Continue?')) return;
    try {
      const res = await fetch(`${API_BASE}/api/demo/reset`, { method: 'POST' });
      if (res.ok) {
        setLastMessage('✅ Demo data cleared!');
        setStats(null);
        setTimeout(() => setLastMessage(''), 3000);
      }
    } catch (error) {
      setLastMessage('❌ Failed to reset demo');
    }
  };

  const totalRequests = stats?.total_requests || 0;
  const threatCount = stats?.threat_count || 0;
  const avgQuality = stats?.avg_quality_score || 0;
  const totalCost = stats?.total_cost_usd || 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="animate-in slide-in-from-top-4 duration-500">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Target className="h-8 w-8 text-cyan-400" />
          Demo Mode - Attack Simulator
        </h1>
        <p className="mt-2 text-sm text-gray-400">
          Test GuardianAI with simulated attack scenarios - no real LLM costs
        </p>
      </div>

      {/* Attack Launcher */}
      <div className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-2 border-blue-500/30 rounded-2xl p-8 shadow-2xl shadow-blue-500/20 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-100">
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-blue-500/10 rounded-lg p-3">
            <Rocket className="h-6 w-6 text-blue-400 hover:animate-pulse" />
          </div>
          <h2 className="text-2xl font-bold text-white">Attack Launcher</h2>
        </div>

        <div className="space-y-6">
          {/* Attack Type Dropdown */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Select Attack Type
            </label>
            <select
              value={selectedAttack}
              onChange={(e) => setSelectedAttack(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-6 py-4 text-white text-lg hover:border-blue-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
            >
              {ATTACK_TYPES.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.icon} {type.name}
                </option>
              ))}
            </select>
          </div>

          {/* Attack Count Slider */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium text-gray-300">
                Number of Attacks
              </label>
              <span className="text-4xl font-bold font-mono text-blue-400">
                {attackCount}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              value={attackCount}
              onChange={(e) => setAttackCount(Number(e.target.value))}
              className="w-full h-3 bg-gray-800 rounded-full appearance-none cursor-pointer slider"
              style={{
                background: `linear-gradient(to right, rgb(59, 130, 246) 0%, rgb(59, 130, 246) ${(attackCount / 20) * 100}%, rgb(31, 41, 55) ${(attackCount / 20) * 100}%, rgb(31, 41, 55) 100%)`
              }}
            />
          </div>

          {/* Launch Button */}
          <button
            onClick={launchAttack}
            disabled={launching}
            className="w-full py-5 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white rounded-xl text-xl font-bold uppercase tracking-wide shadow-2xl shadow-red-500/50 hover:shadow-red-500/70 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 group"
          >
            {launching ? (
              <>
                <div className="animate-spin rounded-full h-6 w-6 border-3 border-white border-t-transparent" />
                Launching...
              </>
            ) : (
              <>
                <Rocket className="h-6 w-6 group-hover:animate-bounce transition-transform" />
                Launch Attack
              </>
            )}
          </button>

          {lastMessage && (
            <div className="text-center text-sm font-medium text-white bg-gray-900/50 rounded-lg py-3 animate-in fade-in duration-200">
              {lastMessage}
            </div>
          )}
        </div>
      </div>

      {/* Preset Scenarios */}
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 delay-200">
        <h2 className="text-xl font-semibold text-white mb-4">Preset Scenarios</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {SCENARIOS.map((scenario) => (
            <button
              key={scenario.id}
              onClick={() => runScenario(scenario.id)}
              disabled={runningScenario?.status === 'running'}
              className={`aspect-square bg-gradient-to-br ${scenario.gradient} border-2 ${scenario.border} rounded-xl p-6 hover:scale-105 hover:shadow-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <div className="h-full flex flex-col items-center justify-center text-center gap-3">
                <div className="text-5xl">{scenario.icon}</div>
                <div className="text-lg font-bold text-white">{scenario.name}</div>
                <div className="text-xs text-gray-400">{scenario.steps} steps</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Scenario Progress */}
      {runningScenario && (
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 border-2 border-blue-500 rounded-xl p-6 shadow-2xl animate-in slide-in-from-bottom-4 duration-300">
          <div className="flex items-center gap-3 mb-4">
            <div className="animate-pulse h-3 w-3 bg-blue-500 rounded-full" />
            <h3 className="text-xl font-semibold text-white">
              Running: {SCENARIOS.find(s => s.id === runningScenario.scenario_id?.split('-')[0])?.name || 'Scenario'}
            </h3>
          </div>

          {/* Progress Bar */}
          <div className="relative h-6 bg-gray-800 rounded-full overflow-hidden mb-4">
            <div
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-600 to-cyan-500 transition-all duration-500 ease-out flex items-center justify-center"
              style={{ width: `${runningScenario.progress_percent}%` }}
            >
              <span className="text-xs font-bold text-white">{runningScenario.progress_percent}%</span>
            </div>
          </div>

          <div className="text-sm text-gray-400 mb-4">
            {runningScenario.current_step_name}
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold font-mono text-blue-400">{runningScenario.current_step}/{runningScenario.total_steps}</div>
              <div className="text-xs text-gray-500">Steps</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold font-mono text-cyan-400">{runningScenario.records_created}</div>
              <div className="text-xs text-gray-500">Records</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold font-mono text-purple-400">{runningScenario.elapsed_seconds}s</div>
              <div className="text-xs text-gray-500">Time</div>
            </div>
          </div>
        </div>
      )}

      {/* Live Metrics */}
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 delay-300">
        <h2 className="text-xl font-semibold text-white mb-4">Live Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            icon={<Activity className="h-6 w-6" />}
            label="Total Requests"
            value={totalRequests.toLocaleString()}
            color="cyan"
          />
          <MetricCard
            icon={<AlertTriangle className="h-6 w-6" />}
            label="Threats Detected"
            value={threatCount.toString()}
            color="red"
          />
          <MetricCard
            icon={<Zap className="h-6 w-6" />}
            label="Avg Quality"
            value={(avgQuality || 0).toFixed(2)}
            color="blue"
          />
          <MetricCard
            icon={<DollarSign className="h-6 w-6" />}
            label="Total Cost"
            value={`$${totalCost.toFixed(2)}`}
            color="amber"
          />
        </div>
      </div>

      {/* Threat Breakdown */}
      {stats && threatCount > 0 && (
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold text-white mb-4">Threat Breakdown</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {Object.entries(stats.threat_breakdown).map(([type, count]) => (
              <div key={type} className="bg-gray-950/50 rounded-lg p-3 border border-gray-700">
                <div className="text-2xl mb-1">{getThreatIcon(type)}</div>
                <div className="text-xl font-bold font-mono text-white">{count}</div>
                <div className="text-xs text-gray-400 capitalize">{type.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Additional Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-6 shadow-xl text-center">
            <div className="text-3xl font-bold font-mono text-purple-400">{Math.round(stats.avg_latency_ms)}ms</div>
            <div className="text-sm text-gray-400 mt-2">Avg Latency</div>
          </div>
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-6 shadow-xl text-center">
            <div className="text-3xl font-bold font-mono text-orange-400">{stats.error_rate_percent.toFixed(1)}%</div>
            <div className="text-sm text-gray-400 mt-2">Error Rate</div>
          </div>
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-6 shadow-xl text-center">
            <div className="text-3xl font-bold font-mono text-red-400">{stats.error_count}</div>
            <div className="text-sm text-gray-400 mt-2">Error Count</div>
          </div>
        </div>
      )}

      {/* Reset Button */}
      <button
        onClick={resetDemo}
        className="w-full py-3 border-2 border-red-500/30 hover:border-red-500/50 text-red-400 hover:text-red-300 rounded-xl font-semibold transition-all duration-200 hover:bg-red-500/10 flex items-center justify-center gap-2"
      >
        <Trash2 className="h-5 w-5" />
        Reset Demo Data
      </button>
    </div>
  );
}

// Metric Card Component
interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}

function MetricCard({ icon, label, value, color }: MetricCardProps) {
  // Extract numeric value for counter animation
  const numericValue = parseFloat(value.replace(/[^0-9.]/g, '')) || 0;
  const prefix = value.match(/^\$/)?.[0] || '';
  const suffix = value.match(/[a-z%]+$/i)?.[0] || '';
  
  const animatedValue = useCountUp(numericValue, 1000, suffix.includes('%') ? 1 : value.includes('.') ? 2 : 0);

  const colorClasses: Record<string, string> = {
    cyan: 'from-cyan-500/10 to-cyan-600/10 border-cyan-500/20 text-cyan-400',
    red: 'from-red-500/10 to-red-600/10 border-red-500/20 text-red-400',
    blue: 'from-blue-500/10 to-blue-600/10 border-blue-500/20 text-blue-400',
    amber: 'from-amber-500/10 to-amber-600/10 border-amber-500/20 text-amber-400',
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} from-gray-900 to-gray-800 border rounded-xl p-6 shadow-xl hover:scale-105 transition-all duration-200`}>
      <div className={`bg-${color}-500/10 rounded-lg p-2 w-fit mb-3`}>
        <div className={colorClasses[color].split(' ')[2]}>{icon}</div>
      </div>
      <div className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-3xl font-bold font-mono text-white">{prefix}{animatedValue}{suffix}</div>
    </div>
  );
}

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
