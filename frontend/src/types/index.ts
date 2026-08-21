export interface RunMetadata {
  run_id: string
  name: string
  description: string
  status: string
  created_at: string
  updated_at: string
  loadrunner_uploaded: boolean
  appdynamics_uploaded: boolean
  analysis_completed: boolean
  rca_completed: boolean
  report_generated: boolean
}

export interface Finding {
  severity: string
  category: string
  component: string
  metric: string
  value: number
  threshold: number
  description: string
  api_name: string
}

export interface AnalysisResult {
  run_id: string
  total_findings: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  sla_violations: Finding[]
  performance_findings: Finding[]
  infrastructure_findings: Finding[]
  bottlenecks: Finding[]
  top_slow_apis: { api: string; p95_ms: number; avg_ms: number }[]
}

export interface RCAResult {
  run_id: string
  root_cause: string
  confidence: number
  severity: string
  contributing_factors: string[]
  evidence: string[]
  affected_components: string[]
  recommendations: string[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}
