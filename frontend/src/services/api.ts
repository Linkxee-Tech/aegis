import type { Incident, MemoryRecord, IncidentReport, SystemHealth, Agent } from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new ApiError(`Request failed: ${res.statusText}`, res.status)
  }
  return res.json()
}

export type SimulateScenario = 'cpu_spike' | 'memory_leak' | 'disk_io' | 'connection_pool' | 'tls_failure'

export const api = {
  getSystemHealth: () => request<SystemHealth>('/health'),
  getAgents: () => request<Agent[]>('/agents'),
  getIncidents: () => request<Incident[]>('/incidents'),
  getIncident: (id: string) => request<Incident>(`/incidents/${id}`),
  getMemory: () => request<MemoryRecord[]>('/memory'),
  getReports: () => request<IncidentReport[]>('/reports'),
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
}

export { ApiError }
