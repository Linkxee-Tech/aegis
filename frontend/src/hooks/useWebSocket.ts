import { useEffect, useRef, useState, useCallback } from 'react'
import { getAuthToken } from '@/services/api'
import { useAuthVersion } from './useAuthSession'

export type WsStatus = 'connecting' | 'open' | 'closed' | 'error'

interface UseWebSocketOptions {
  url: string
  onMessage?: (data: unknown) => void
  enabled?: boolean
}

/**
 * Connects to the Aegis orchestrator's WebSocket stream for live agent/incident
 * events. Falls back gracefully (status stays "closed") when no backend is running,
 * which is expected in frontend-only / demo mode.
 */
export function useWebSocket({ url, onMessage, enabled = true }: UseWebSocketOptions) {
  const [status, setStatus] = useState<WsStatus>('connecting')
  const wsRef = useRef<WebSocket | null>(null)
  const authVersion = useAuthVersion()

  useEffect(() => {
    if (!enabled) return
    let didCancel = false

    try {
      const authToken = getAuthToken()
      const wsUrl = new URL(url)
      if (authToken) {
        wsUrl.searchParams.set('token', authToken)
      }
      const ws = new WebSocket(wsUrl.toString())
      wsRef.current = ws

      ws.onopen = () => !didCancel && setStatus('open')
      ws.onclose = () => !didCancel && setStatus('closed')
      ws.onerror = () => !didCancel && setStatus('error')
      ws.onmessage = (event) => {
        if (didCancel) return
        try {
          const data = JSON.parse(event.data)
          onMessage?.(data)
        } catch {
          onMessage?.(event.data)
        }
      }
    } catch {
      setStatus('error')
    }

    return () => {
      didCancel = true
      wsRef.current?.close()
    }
  }, [url, enabled, authVersion])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [])

  return { status, send }
}
