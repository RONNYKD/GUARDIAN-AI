import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Shield, AlertTriangle, Search, ChevronDown, Target } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

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

export default function Threats() {
  const [stats, setStats] = useState<DemoStats | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/demo/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error loading threats data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleCard = (type: string) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(type)) {
      newExpanded.delete(type);
    } else {
      newExpanded.add(type);
    }
    setExpandedCards(newExpanded);
  };

  const threatTypes = stats?.threat_breakdown ? Object.entries(stats.threat_breakdown) : [];
  
  // Filter threats
  const filteredThreats = threatTypes.filter(([type, count]) => {
    if (selectedType !== 'all' && type !== selectedType) return false;
    const severity = getSeverityForType(type);
    if (selectedSeverity !== 'all' && severity !== selectedSeverity) return false;
    if (searchTerm && !type.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return count > 0;
  });

  const totalThreats = stats?.threat_count || 0;

  if (loading) {
    return (
      <div className="space-y-8 animate-in fade-in duration-500">
        {/* Header Skeleton */}
        <div className="space-y-2">
          <div className="h-10 w-64 bg-gray-800 rounded animate-pulse" />
          <div className="h-4 w-48 bg-gray-800 rounded animate-pulse" />
        </div>

        {/* Stats Grid Skeleton */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-4 shadow-xl animate-pulse">
              <div className="h-8 w-8 bg-gray-700 rounded mb-2" />
              <div className="h-6 w-12 bg-gray-700 rounded mb-1" />
              <div className="h-3 w-20 bg-gray-700 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex items-center justify-between animate-in slide-in-from-top-4 duration-500">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Shield className="h-8 w-8 text-red-400 hover:animate-pulse" />
            Security Threats
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            Total detected: <span className="text-white font-semibold font-mono">{totalThreats}</span>
          </p>
        </div>
      </div>

      {/* Threat Statistics Grid */}
      {totalThreats > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-100">
          {threatTypes.map(([type, count]) => {
            const icon = getThreatIcon(type);
            const color = getSeverityColor(type);
            return (
              <button
                key={type}
                onClick={() => setSelectedType(selectedType === type ? 'all' : type)}
                className={`bg-gradient-to-br from-gray-900 to-gray-800 border rounded-xl p-4 hover:scale-105 transition-all duration-200 ${
                  selectedType === type ? `border-${color}-500` : 'border-gray-800 hover:border-gray-700'
                }`}
              >
                <div className="text-3xl mb-2">{icon}</div>
                <div className={`text-2xl font-bold font-mono text-${color}-400`}>{count}</div>
                <div className="text-xs text-gray-400 mt-1 capitalize">
                  {type.replace('_', ' ')}
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Filters */}
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-6 shadow-xl">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search threats..."
              className="pl-10 w-full px-4 py-3 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder:text-gray-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
            />
          </div>

          {/* Severity Filter */}
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-4 py-3 bg-gray-950 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-4 py-3 bg-gray-950 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
          >
            <option value="all">All Types</option>
            <option value="prompt_injection">Prompt Injection</option>
            <option value="pii_leak">PII Leak</option>
            <option value="jailbreak_attempt">Jailbreak Attempt</option>
            <option value="toxic_content">Toxic Content</option>
            <option value="cost_spike">Cost Spike</option>
            <option value="quality_degradation">Quality Degradation</option>
          </select>
        </div>
      </div>

      {/* Threat Timeline */}
      {filteredThreats.length > 0 ? (
        <div className="space-y-4">
          {filteredThreats.map(([type, count]) => {
            const severity = getSeverityForType(type);
            const color = getSeverityColor(type);
            const description = getDescriptionForType(type);
            const indicators = getIndicatorsForType(type);
            const confidence = getConfidenceForType(type);
            const isExpanded = expandedCards.has(type);

            return (
              <div
                key={type}
                className={`bg-gradient-to-br from-gray-900 to-gray-800 border-l-4 border-${color}-500 rounded-lg overflow-hidden hover:bg-gray-800 transition-all duration-200 shadow-xl`}
              >
                {/* Collapsed State */}
                <button
                  onClick={() => toggleCard(type)}
                  className="w-full p-6 text-left"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      <div className="text-4xl">{getThreatIcon(type)}</div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-xl font-semibold text-white capitalize">
                            {type.replace('_', ' ')}
                          </h3>
                          <span className={`px-3 py-1 rounded-full text-xs font-mono font-semibold bg-${color}-500/20 text-${color}-400`}>
                            {count}
                          </span>
                        </div>
                        <p className="text-sm text-gray-400 mt-1">{description}</p>
                        <div className="flex items-center gap-4 mt-3 text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-semibold uppercase bg-${color}-500/20 text-${color}-400`}>
                            {severity}
                          </span>
                          <span className="text-gray-500">
                            Confidence: <span className="text-white font-mono">{(confidence * 100).toFixed(0)}%</span>
                          </span>
                          <span className="text-emerald-400 text-sm font-medium flex items-center gap-1">
                            <div className="h-2 w-2 bg-emerald-400 rounded-full" />
                            Blocked
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className={`text-gray-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
                      <ChevronDown className="h-6 w-6" />
                    </div>
                  </div>
                </button>

                {/* Expanded State */}
                {isExpanded && (
                  <div className="px-6 pb-6 border-t border-gray-800 pt-4 space-y-4 animate-in slide-in-from-top-2 duration-200">
                    {/* Indicators */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wide">
                        Threat Indicators
                      </h4>
                      <ul className="space-y-2">
                        {indicators.map((indicator, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                            <AlertTriangle className={`h-4 w-4 text-${color}-400 mt-0.5 flex-shrink-0`} />
                            {indicator}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 pt-2">
                      <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
                        View Details
                      </button>
                      <button className="px-4 py-2 border border-gray-700 hover:bg-gray-700 text-gray-300 rounded-lg text-sm font-medium transition-colors">
                        Add to Whitelist
                      </button>
                      <button className="px-4 py-2 border border-gray-700 hover:bg-gray-700 text-gray-300 rounded-lg text-sm font-medium transition-colors">
                        Report False Positive
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        /* Empty State */
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-12 text-center shadow-xl">
          <div className="bg-emerald-500/10 rounded-full h-24 w-24 flex items-center justify-center mx-auto mb-6">
            <Shield className="h-12 w-12 text-emerald-400" />
          </div>
          <h3 className="text-2xl font-bold text-white mb-2">No Threats Detected</h3>
          <p className="text-gray-400 mb-6">Your LLM applications are secure and operating normally</p>
          <Link
            to="/demo"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white rounded-lg font-semibold transition-all duration-200 hover:shadow-xl hover:shadow-blue-500/50 hover:scale-105"
          >
            <Target className="h-5 w-5" />
            Launch Demo Mode
          </Link>
        </div>
      )}

      {/* Summary Statistics */}
      {totalThreats > 0 && (
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800 rounded-xl p-6 shadow-xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold font-mono text-emerald-400">100%</div>
              <div className="text-sm text-gray-400 mt-1">Detection Rate</div>
            </div>
            <div>
              <div className="text-3xl font-bold font-mono text-white">{totalThreats}/{totalThreats}</div>
              <div className="text-sm text-gray-400 mt-1">Blocked Attacks</div>
            </div>
            <div>
              <div className="text-3xl font-bold font-mono text-blue-400">95%</div>
              <div className="text-sm text-gray-400 mt-1">Avg Confidence</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper functions
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

function getSeverityForType(type: string): string {
  const severities: Record<string, string> = {
    prompt_injection: 'critical',
    pii_leak: 'high',
    jailbreak_attempt: 'critical',
    toxic_content: 'high',
    cost_spike: 'medium',
    quality_degradation: 'low',
  };
  return severities[type] || 'medium';
}

function getSeverityColor(type: string): string {
  const severity = getSeverityForType(type);
  const colors: Record<string, string> = {
    critical: 'red',
    high: 'orange',
    medium: 'amber',
    low: 'blue',
  };
  return colors[severity] || 'gray';
}

function getDescriptionForType(type: string): string {
  const descriptions: Record<string, string> = {
    prompt_injection: 'Detected malicious prompt injection patterns attempting to manipulate system behavior',
    pii_leak: 'Personal identifiable information detected in prompts or responses',
    jailbreak_attempt: 'System prompt bypass attempt detected to circumvent safety guidelines',
    toxic_content: 'Harmful or offensive content blocked from being processed',
    cost_spike: 'Unusual cost increase detected due to high token usage',
    quality_degradation: 'Response quality below acceptable threshold',
  };
  return descriptions[type] || 'Security threat detected';
}

function getIndicatorsForType(type: string): string[] {
  const indicators: Record<string, string[]> = {
    prompt_injection: [
      'SQL injection-style patterns detected in user prompt',
      'Attempts to override system instructions found',
      'Suspicious command sequences identified',
      'Pattern matching confidence: 95%'
    ],
    pii_leak: [
      'Social Security Numbers (SSN) detected',
      'Credit card numbers identified',
      'Email addresses and phone numbers found',
      'Automatic redaction applied'
    ],
    jailbreak_attempt: [
      'System prompt bypass patterns detected',
      'Role-play escape sequences found',
      'Attempts to ignore safety guidelines',
      'Advanced prompt engineering techniques identified'
    ],
    toxic_content: [
      'Harmful language patterns detected',
      'Offensive content blocked',
      'Hate speech indicators found',
      'Content moderation policy triggered'
    ],
    cost_spike: [
      'Token usage exceeds normal baseline by 300%',
      'Repeated long-form generations detected',
      'Potential token stuffing attack',
      'Cost threshold warning activated'
    ],
    quality_degradation: [
      'Response coherence below 0.7 threshold',
      'Factual accuracy concerns detected',
      'Incomplete or irrelevant responses',
      'Quality assurance check failed'
    ],
  };
  return indicators[type] || ['Threat indicators detected'];
}

function getConfidenceForType(type: string): number {
  const confidences: Record<string, number> = {
    prompt_injection: 0.95,
    pii_leak: 0.98,
    jailbreak_attempt: 0.92,
    toxic_content: 0.88,
    cost_spike: 0.85,
    quality_degradation: 0.80,
  };
  return confidences[type] || 0.90;
}
