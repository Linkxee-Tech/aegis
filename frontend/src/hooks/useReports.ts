import { useCallback, useEffect, useState } from 'react'
import type { IncidentReport } from '@/types'
import { reports as mockReports } from '@/data/mockData'
import { ApiError, api } from '@/services/api'
import { useAuthVersion } from './useAuthSession'

export function useReports() {
  const [reports, setReports] = useState<IncidentReport[]>(mockReports)
  const [isLive, setIsLive] = useState(false)
  const [loading, setLoading] = useState(true)
  const authVersion = useAuthVersion()

  const refresh = useCallback(async () => {
    try {
      const data = await api.getReports()
      if (data?.length) {
        setReports(data)
        setIsLive(true)
      }
    } catch (error) {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
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

  return { reports, isLive, loading, refresh }
}
