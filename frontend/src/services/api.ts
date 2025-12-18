const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface TelemetryRecord {
  trace_id: string
  timestamp: string
  model: string
  prompt: string
  response: string
  input_tokens: number
  output_tokens: number
  latency_ms: number
  cost_usd: number
  quality_score: number
  user_id?: string
  session_id?: string
  metadata?: Record<string, any>
}

export interface Threat {
  id: string
  trace_id: string
  type: string
  severity: string
  description: string
  detected_at: string
  confidence: number
  metadata?: Record<string, any>
}

export interface Incident {
  id: string
  title: string
  description: string
  severity: string
  status: string
  created_at: string
  updated_at: string
  resolved_at?: string
  threat_ids: string[]
  auto_remediated: boolean
  remediation_actions?: string[]
}

export interface HealthScore {
  score: number
  security_score: number
  quality_score: number
  performance_score: number
  cost_score: number
  timestamp: string
}

export interface MetricsSummary {
  total_requests: number
  total_cost: number
  avg_latency: number
  avg_quality: number
  threat_count: number
  incident_count: number
  error_rate: number
  period_start: string
  period_end: string
}

class ApiService {
  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Health endpoints
  async getHealth() {
    return this.fetch<{ status: string; timestamp: string }>('/health')
  }

  async getHealthScore(): Promise<HealthScore> {
    return this.fetch<HealthScore>('/api/health/score')
  }

  // Metrics endpoints
  async getMetrics(hours: number = 24): Promise<MetricsSummary> {
    return this.fetch<MetricsSummary>(`/api/metrics?hours=${hours}`)
  }

  async getTelemetry(limit: number = 100): Promise<TelemetryRecord[]> {
    return this.fetch<TelemetryRecord[]>(`/api/metrics/telemetry?limit=${limit}`)
  }

  // Incident endpoints
  async getIncidents(status?: string): Promise<Incident[]> {
    const query = status ? `?status=${status}` : ''
    return this.fetch<Incident[]>(`/api/incidents${query}`)
  }

  async getIncident(id: string): Promise<Incident> {
    return this.fetch<Incident>(`/api/incidents/${id}`)
  }

  async updateIncident(id: string, updates: Partial<Incident>): Promise<Incident> {
    return this.fetch<Incident>(`/api/incidents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })
  }

  async autoRemediate(id: string): Promise<{ success: boolean; actions: string[] }> {
    return this.fetch<{ success: boolean; actions: string[] }>(
      `/api/incidents/${id}/remediate`,
      { method: 'POST' }
    )
  }

  // Threat endpoints
  async getThreats(limit: number = 100): Promise<Threat[]> {
    // This would be a custom endpoint you'd add to backend
    return this.fetch<Threat[]>(`/api/threats?limit=${limit}`)
  }

  // Demo endpoints
  async simulateAttack(attackType: string): Promise<{ trace_id: string; detected: boolean }> {
    return this.fetch<{ trace_id: string; detected: boolean }>('/api/demo/attack', {
      method: 'POST',
      body: JSON.stringify({ attack_type: attackType }),
    })
  }
}

export const apiService = new ApiService()
