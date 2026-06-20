import type { SystemHealth } from '@/types'

interface SystemHealthBarProps {
  health: SystemHealth
}

export function SystemHealthBar({ health }: SystemHealthBarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-graphite-700 bg-graphite-900 px-5 py-3.5">
      <div className="flex items-center gap-3">
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-pulse-slow rounded-full bg-signal-remediation opacity-75" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-signal-remediation" />
        </span>
        <span className="text-[14px] font-medium text-bone-100">
          {health.allAgentsOperational ? 'All agents operational' : 'Degraded — check agent status'}
        </span>
      </div>
      <div className="flex items-center gap-5 font-mono-data text-[12.5px] text-bone-500">
        <span>
          Last incident <span className="text-bone-300">{health.lastIncidentAgo}</span>
        </span>
        <span className="hidden h-3 w-px bg-graphite-600 sm:block" />
        <span className="hidden sm:inline">
          Uptime <span className="text-bone-300">{health.uptimePercentage}%</span>
        </span>
        <span className="hidden h-3 w-px bg-graphite-600 sm:block" />
        <span>
          Active <span className="text-signal-amber">{health.activeIncidentCount}</span>
        </span>
      </div>
    </div>
  )
}
