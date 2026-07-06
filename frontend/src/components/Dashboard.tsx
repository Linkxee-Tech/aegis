import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { SystemHealthBar } from './SystemHealthBar'
import { AgentStatusGrid } from './AgentStatus'
import { ActiveIncidentPanel } from './ActiveIncidentPanel'
import { HistoryTimeline } from './HistoryTimeline'
import { MemorySummaryBar } from './MemorySummaryBar'
import { SimulateIncident } from './SimulateIncident'
import { useIncidents } from '@/hooks/useIncidents'
import { useAgents, useSystemHealth, useMemoryRecords } from '@/hooks/useLiveData'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useToast } from '@/hooks/useToast'
import { ApiError } from '@/services/api'
import { IconCheck } from './icons'

const WS_BASE =
  import.meta.env.VITE_WS_URL?.replace('/ws', '') ||
  `ws://${typeof window !== 'undefined' ? window.location.host : 'localhost:8000'}`

export function Dashboard() {
  const navigate = useNavigate()
  const { incidents, isLive: incidentsLive, approve, reject, refresh: refreshIncidents } = useIncidents()
  const { agents } = useAgents()
  const { systemHealth } = useSystemHealth()
  const { memoryRecords } = useMemoryRecords()
  const { toast, showToast } = useToast()

  const activeIncident = incidents.find((i) => !['resolved', 'auto_resolved', 'rejected'].includes(i.status))

  // Use the protocol-compatible per-incident WebSocket when there's an active incident,
  // falling back to the general /ws channel when all clear.
  const wsUrl = activeIncident ? `${WS_BASE}/ws/${activeIncident.id}` : `${WS_BASE}/ws`

  const { status: wsStatus } = useWebSocket({
    url: wsUrl,
    enabled: incidentsLive,
    onMessage: () => {
      refreshIncidents()
    },
  })

  useEffect(() => {
    if (wsStatus === 'open') {
      showToast('Connected to live incident stream')
    }
  }, [wsStatus, showToast])

  const historyIncidents = incidents

  async function handleApprove(incidentId: string) {
    try {
      await approve(incidentId)
      showToast('Remediation approved — executing on live server')
    } catch (error) {
      if (error instanceof ApiError && error.status === 403) {
        showToast('Approval blocked — your token does not have operator access')
        return
      }
      if (error instanceof ApiError && error.status === 401) {
        showToast('Approval blocked — add an operator token in Settings')
        return
      }
      showToast('Approval failed — the request may have expired')
    }
  }

  async function handleReject(incidentId: string, reason: string) {
    try {
      await reject(incidentId, reason)
      showToast(reason ? 'Sent back to Diagnostician with your note' : 'Remediation rejected')
    } catch (error) {
      if (error instanceof ApiError && error.status === 403) {
        showToast('Rejection blocked — your token does not have operator access')
        return
      }
      if (error instanceof ApiError && error.status === 401) {
        showToast('Rejection blocked — add an operator token in Settings')
        return
      }
      showToast('Rejection failed — please try again')
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SystemHealthBar health={systemHealth} />
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/integrations')}
            className="flex items-center gap-1.5 rounded-md border border-graphite-600 bg-graphite-800 px-3 py-1.5 text-[12px] font-medium text-bone-300 transition-colors hover:bg-graphite-700 hover:text-bone-100"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            Integration Guide
          </button>
          <button
            onClick={() => navigate('/guide')}
            className="flex items-center gap-1.5 rounded-md border border-graphite-600 bg-graphite-800 px-3 py-1.5 text-[12px] font-medium text-bone-300 transition-colors hover:bg-graphite-700 hover:text-bone-100"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            User Guide
          </button>
          <SimulateIncident isLive={incidentsLive} onTriggered={showToast} />
        </div>
      </div>
      <AgentStatusGrid agents={agents} />

      {activeIncident ? (
        <ActiveIncidentPanel
          incident={activeIncident}
          onApprove={() => handleApprove(activeIncident.id)}
          onReject={(reason) => handleReject(activeIncident.id, reason)}
        />
      ) : (
        <div className="rounded-lg border border-signal-remediation/30 bg-graphite-900 p-6 text-center">
          <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-signal-remediation/10">
            <IconCheck className="h-5 w-5 text-signal-remediation" />
          </div>
          <p className="mt-3 text-[14px] font-medium text-bone-100">No active incidents — all systems nominal</p>
          <p className="mt-1 text-[12.5px] text-bone-500">
            The Detective Agent is watching. You'll see a panel here the moment something needs attention.
          </p>
        </div>
      )}

      <HistoryTimeline incidents={historyIncidents} />
      <MemorySummaryBar records={memoryRecords} />

      {toast && (
        <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-md border border-graphite-600 bg-graphite-800 px-4 py-3 text-[13px] text-bone-100 shadow-2xl">
          {toast}
        </div>
      )}
    </div>
  )
}
