import { useCallback, useEffect, useState } from 'react'
import type { Agent, SystemHealth, MemoryRecord, IncidentReport } from '@/types'
import { agents as demoAgents, systemHealth as demoSystemHealth, memoryRecords as demoMemoryRecords, reports as demoReports } from '@/data/mockData'
import { api } from '@/services/api'

/**
 * Shared shape for "fetch from the live API, fall back to demo data" hooks.
 * Each of useAgents / useSystemHealth / useMemoryRecords / useReports follows
 * this same pattern so every dashboard page behaves consistently whether or
 * not a backend is actually running.
 */
function useLiveOrDemo<T>(fetcher: () => Promise<T>, demoData: T) {
  const [data, setData] = useState<T>(demoData)
  const [isLive, setIsLive] = useState(false)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const result = await fetcher()
      setData(result)
      setIsLive(true)
    } catch {
      setIsLive(false)
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { data, isLive, loading, refresh }
}

export function useAgents() {
  const { data, isLive, loading, refresh } = useLiveOrDemo<Agent[]>(api.getAgents, demoAgents)
  return { agents: data, isLive, loading, refresh }
}

export function useSystemHealth() {
  const { data, isLive, loading, refresh } = useLiveOrDemo<SystemHealth>(api.getSystemHealth, demoSystemHealth)
  return { systemHealth: data, isLive, loading, refresh }
}

export function useMemoryRecords() {
  const { data, isLive, loading, refresh } = useLiveOrDemo<MemoryRecord[]>(api.getMemory, demoMemoryRecords)
  return { memoryRecords: data, isLive, loading, refresh }
}

export function useReports() {
  const { data, isLive, loading, refresh } = useLiveOrDemo<IncidentReport[]>(api.getReports, demoReports)
  return { reports: data, isLive, loading, refresh }
}
