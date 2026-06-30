import { useState } from 'react'
import { api, ApiError, type SimulateScenario } from '@/services/api'
import { cx } from '@/utils/format'

interface SimulateIncidentProps {
  onTriggered: (message: string) => void
  isLive: boolean
}

const SCENARIOS: { value: SimulateScenario; label: string; icon: string; color: string }[] = [
  { value: 'cpu_spike', label: 'CPU Spike', icon: '📈', color: 'text-signal-danger' },
  { value: 'memory_leak', label: 'Memory Leak', icon: '🧠', color: 'text-signal-diagnostician' },
  { value: 'disk_io', label: 'Disk I/O Saturation', icon: '💾', color: 'text-signal-reporter' },
  { value: 'connection_pool', label: 'Connection Pool Exhaustion', icon: '🔗', color: 'text-signal-detective' },
  { value: 'tls_failure', label: 'TLS Handshake Failure', icon: '🔒', color: 'text-signal-remediation' },
]

export function SimulateIncident({ onTriggered, isLive }: SimulateIncidentProps) {
  const [open, setOpen] = useState(false)
  const [running, setRunning] = useState(false)
  const [selected, setSelected] = useState<SimulateScenario>('cpu_spike')

  async function handleSimulate() {
    setRunning(true)
    try {
      if (isLive) {
        const result = await api.simulateIncident(selected)
        onTriggered(result.message)
      } else {
        // Demo-mode: simulate locally without a backend call
        onTriggered(`Demo mode: simulating "${selected}" — connect the backend to run the real pipeline`)
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 403) {
        onTriggered('Simulation blocked — you need an operator token in Settings')
      } else if (error instanceof ApiError && error.status === 401) {
        onTriggered('Simulation blocked — sign in with an operator token in Settings')
      } else {
        onTriggered('Could not trigger simulation — is the backend running?')
      }
    } finally {
      setRunning(false)
      setOpen(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={cx(
          'flex items-center gap-2 rounded-md border px-3.5 py-2 text-[13px] font-semibold transition-all',
          'border-signal-danger/50 bg-signal-danger/10 text-signal-danger',
          'hover:border-signal-danger hover:bg-signal-danger/20',
          running && 'animate-pulse cursor-not-allowed opacity-60'
        )}
        disabled={running}
      >
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal-danger opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-signal-danger" />
        </span>
        {running ? 'Triggering…' : 'Simulate Incident'}
      </button>

      {open && !running && (
        <div className="absolute right-0 top-full z-50 mt-1.5 w-64 rounded-lg border border-graphite-600 bg-graphite-800 p-2 shadow-2xl">
          <p className="mb-2 px-2 font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500">
            Choose scenario
          </p>
          {SCENARIOS.map((s) => (
            <button
              key={s.value}
              onClick={() => setSelected(s.value)}
              className={cx(
                'flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-[13px] transition-colors',
                selected === s.value ? 'bg-graphite-700 text-bone-100' : 'text-bone-300 hover:bg-graphite-700/60'
              )}
            >
              <span>{s.icon}</span>
              <span className={cx('font-medium', selected === s.value && s.color)}>{s.label}</span>
            </button>
          ))}
          <div className="mt-2 border-t border-graphite-700 pt-2">
            <button
              onClick={handleSimulate}
              className="w-full rounded-md bg-signal-danger px-3 py-2 text-[13px] font-semibold text-graphite-950 hover:bg-signal-danger/90"
            >
              Trigger on prod-ecs-03 →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
