import { useEffect } from 'react'
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
import { IconCheck } from './icons'

const WS_BASE = import.meta.env.VITE_WS_URL?.replace('/ws', '') ||
  `ws://${typeof window !== 'undefined' ? window.location.host : 'localhost:8000'}`

export function Dashboard() {
  const { incidents, isLive: incidentsLive, approve, reject, refresh: refreshIncidents } = useIncidents()
  const { agents } = useAgents()
  const { systemHealth } = useSystemHealth()
  const { memoryRecords } = useMemoryRecords()
  const { toast, showToast } = useToast()

  const activeIncident = incidents.find((i) => !['resolved', 'auto_resolved', 'rejected'].includes(i.status))

  // Use the protocol-compatible per-incident WebSocket when there's an active incident,
  // falling back to the general /ws channel when all clear.
  const wsUrl = activeIncident
    ? `${WS_BASE}/ws/${activeIncident.id}`
    : `${WS_BASE}/ws`

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
  }, [wsStatus])
  const historyIncidents = incidents

  async function handleApprove(incidentId: string) {
    try {
      await approve(incidentId)
      showToast('Remediation approved — executing on live server')
    } catch {
      showToast('Approval failed — the request may have expired')
    }
  }

  async function handleReject(incidentId: string, reason: string) {
    try {
      await reject(incidentId, reason)
      showToast(reason ? 'Sent back to Diagnostician with your note' : 'Remediation rejected')
    } catch {
      showToast('Rejection failed — please try again')
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SystemHealthBar health={systemHealth} />
        <SimulateIncident isLive={incidentsLive} onTriggered={showToast} />
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
          <p className="mt-3 text-[14px] font-medium text-bone-100">
            No active incidents — all systems nominal
          </p>
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
