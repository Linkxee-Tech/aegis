import { useEffect, useState } from 'react'
import { AUTH_CHANGED_EVENT, clearAuthToken, getAuthToken, setAuthToken } from '@/services/api'

export function useAuthSession() {
  const [token, setTokenState] = useState(getAuthToken())

  useEffect(() => {
    const sync = () => setTokenState(getAuthToken())
    window.addEventListener('storage', sync)
    window.addEventListener(AUTH_CHANGED_EVENT, sync)
    return () => {
      window.removeEventListener('storage', sync)
      window.removeEventListener(AUTH_CHANGED_EVENT, sync)
    }
  }, [])

  return {
    token,
    setToken: (nextToken: string) => {
      setAuthToken(nextToken)
      setTokenState(nextToken.trim())
    },
    clearToken: () => {
      clearAuthToken()
      setTokenState('')
    },
  }
}

export function useAuthVersion() {
  const [version, setVersion] = useState(0)

  useEffect(() => {
    const bump = () => setVersion((value) => value + 1)
    window.addEventListener('storage', bump)
    window.addEventListener(AUTH_CHANGED_EVENT, bump)
    return () => {
      window.removeEventListener('storage', bump)
      window.removeEventListener(AUTH_CHANGED_EVENT, bump)
    }
  }, [])

  return version
}
