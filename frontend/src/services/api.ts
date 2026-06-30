import type { AdminOverview, Incident, MemoryRecord, IncidentReport, SystemHealth, Agent } from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'
const AUTH_STORAGE_KEY = 'aegis.apiToken'
export const AUTH_CHANGED_EVENT = 'aegis-auth-changed'

class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function emitAuthChanged() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT))
  }
}

export function getAuthToken() {
  if (typeof window === 'undefined') return ''
  return window.localStorage.getItem(AUTH_STORAGE_KEY) || ''
}

export function setAuthToken(token: string) {
  if (typeof window === 'undefined') return
  const cleaned = token.trim()
  if (cleaned) {
    window.localStorage.setItem(AUTH_STORAGE_KEY, cleaned)
  } else {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
  }
  emitAuthChanged()
}

export function clearAuthToken() {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(AUTH_STORAGE_KEY)
  emitAuthChanged()
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const { headers: optionHeaders, ...requestOptions } = options || {}
  const headers = new Headers(optionHeaders || {})
  headers.set('Content-Type', 'application/json')

  const authToken = getAuthToken()
  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`)
  }

  const res = await fetch(`${API_BASE}${path}`, {
    headers,
    ...requestOptions,
  })
  if (!res.ok) {
    throw new ApiError(`Request failed: ${res.statusText}`, res.status)
  }
  return res.json()
}

function buildAuthHeaders(extraHeaders?: HeadersInit) {
  const headers = new Headers(extraHeaders || {})
  const authToken = getAuthToken()
  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`)
  }
  return headers
}

function parseFilename(contentDisposition: string | null, fallback: string) {
  if (!contentDisposition) return fallback
  const matches = [
    /filename\*=(?:UTF-8''|")?([^";]+)"?/i.exec(contentDisposition),
    /filename="([^"]+)"/i.exec(contentDisposition),
    /filename=([^;]+)/i.exec(contentDisposition),
  ]
  for (const match of matches) {
    if (match?.[1]) {
      try {
        return decodeURIComponent(match[1].trim())
      } catch {
        return match[1].trim()
      }
    }
  }
  return fallback
}

export type SimulateScenario = 'cpu_spike' | 'memory_leak' | 'disk_io' | 'connection_pool' | 'tls_failure'

export const api = {
  getSystemHealth: () => request<SystemHealth>('/health'),
  getAgents: () => request<Agent[]>('/agents'),
  getIncidents: () => request<Incident[]>('/incidents'),
  getIncident: (id: string) => request<Incident>(`/incidents/${id}`),
  getMemory: () => request<MemoryRecord[]>('/memory'),
  getReports: () => request<IncidentReport[]>('/reports'),
  getAdminOverview: () => request<AdminOverview>('/admin/overview'),
  approveRemediation: (incidentId: string) =>
    request<{ success: boolean }>(`/incidents/${incidentId}/approve`, { method: 'POST' }),
  rejectRemediation: (incidentId: string, reason?: string) =>
    request<{ success: boolean }>(`/incidents/${incidentId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  simulateIncident: (scenario: SimulateScenario = 'cpu_spike', server?: string, service?: string) =>
    request<{ success: boolean; message: string; scenario: string }>('/simulate', {
      method: 'POST',
      body: JSON.stringify({ scenario, server, service }),
    }),
  downloadReport: (reportId: string) => `${API_BASE}/reports/${reportId}/download`,
  fetchReportDownload: async (reportId: string) => {
    const res = await fetch(`${API_BASE}/reports/${reportId}/download`, {
      headers: buildAuthHeaders(),
    })
    if (!res.ok) {
      throw new ApiError(`Request failed: ${res.statusText}`, res.status)
    }

    const filename = parseFilename(
      res.headers.get('content-disposition'),
      `report-${reportId}.pdf`
    )
    return {
      blob: await res.blob(),
      filename,
      ossUrl: res.headers.get('x-oss-url'),
    }
  },
}

export { ApiError }
