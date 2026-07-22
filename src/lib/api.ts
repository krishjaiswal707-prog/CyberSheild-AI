const DEFAULT_API = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

let _baseUrl = DEFAULT_API

export function getApiBaseUrl(): string {
  return _baseUrl
}

export function setApiBaseUrl(url: string): void {
  _baseUrl = url.replace(/\/+$/, '')
}

export interface ApiAnalysisRequest {
  text: string
  user_id?: string
}

export interface ApiAnalysisResponse {
  analysis_id: string
  risk_score: number
  risk_tier: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  confidence: number
  matched_red_flags: string[]
  explanation: string
  language: string
  rule_override_fired: boolean
  rule_fired_name: string | null
  checklist_triggered: boolean
}

export interface ApiHealthResponse {
  status: string
  version: string
  timestamp: string
  claude_model: string
  environment: string
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${_baseUrl}${path}`
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${body || res.statusText}`)
  }
  return res.json() as Promise<T>
}

export async function checkHealth(): Promise<ApiHealthResponse> {
  return request<ApiHealthResponse>('/health')
}

export async function analyzeMessage(
  text: string,
  userId = 'anonymous',
): Promise<ApiAnalysisResponse> {
  return request<ApiAnalysisResponse>('/api/v1/analysis/message', {
    method: 'POST',
    body: JSON.stringify({ text, user_id: userId } satisfies ApiAnalysisRequest),
  })
}

export async function analyzeCall(
  description: string,
  userId = 'anonymous',
): Promise<ApiAnalysisResponse> {
  return request<ApiAnalysisResponse>('/api/v1/analysis/call', {
    method: 'POST',
    body: JSON.stringify({ description, user_id: userId }),
  })
}
