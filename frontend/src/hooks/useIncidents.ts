import { useCallback, useEffect, useState } from 'react'
import type { Incident } from '@/types'
import { incidentHistory } from '@/data/mockData'
import { ApiError, api } from '@/services/api'
import { useAuthVersion } from './useAuthSession'

/**
 * Provides incident data to components. Attempts to load from the live API;
 * if unavailable (e.g. backend not running yet), falls back to demo data so
 * the interface remains fully explorable during frontend development.
 *
 * Also exposes `approve` / `reject` actions that call the real API when a
 * backend is reachable. In demo mode (no backend), they fall back to a local
 * optimistic update so the approval flow is still fully clickable for a
 * standalone walkthrough.
 */
export function useIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>(incidentHistory)
  const [isLive, setIsLive] = useState(false)
  const [loading, setLoading] = useState(true)
  const authVersion = useAuthVersion()

  const refresh = useCallback(async () => {
    try {
      const data = await api.getIncidents()
      if (data?.length) {
        data.sort((a, b) => new Date(b.detectedAt).getTime() - new Date(a.detectedAt).getTime())
        setIncidents(data)
        setIsLive(true)
      }
    } catch (error) {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        // The backend is reachable but the current token does not authorize access.
        setIsLive(true)
      } else {
        // expected when no backend is running — demo data remains active
        setIsLive(false)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh, authVersion])

  const approve = useCallback(
    async (incidentId: string) => {
      if (isLive) {
        await api.approveRemediation(incidentId)
        await refresh()
        return
      }
      // Demo-mode fallback: simulate the transition locally.
      setIncidents((prev) =>
        prev.map((incident) =>
          incident.id === incidentId
            ? {
                ...incident,
                status: 'remediating',
                timeline: incident.timeline.map((event) =>
                  event.status === 'in_progress'
                    ? { ...event, status: 'complete', title: 'Fix approved & executed' }
                    : event.status === 'pending'
                    ? { ...event, status: 'in_progress', timestamp: new Date().toISOString() }
                    : event
                ),
              }
            : incident
        )
      )
    },
    [isLive, refresh]
  )

  const reject = useCallback(
    async (incidentId: string, reason?: string) => {
      if (isLive) {
        await api.rejectRemediation(incidentId, reason)
        await refresh()
        return
      }
      setIncidents((prev) =>
        prev.map((incident) => (incident.id === incidentId ? { ...incident, status: 'rejected' } : incident))
      )
    },
    [isLive, refresh]
  )

  return { incidents, isLive, loading, refresh, approve, reject }
}
