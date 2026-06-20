import { useCallback, useRef, useState } from 'react'

/**
 * Minimal toast hook: call showToast(message) to display a transient message
 * at the bottom of the screen for ~3.2s. Shared across pages so every
 * fire-and-forget action (approve, reject, export, etc.) gives the same
 * lightweight feedback instead of failing silently.
 */
export function useToast() {
  const [toast, setToast] = useState<string | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showToast = useCallback((message: string, durationMs = 3200) => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    setToast(message)
    timeoutRef.current = setTimeout(() => setToast(null), durationMs)
  }, [])

  return { toast, showToast }
}
