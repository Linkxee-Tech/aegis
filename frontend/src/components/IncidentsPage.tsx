import { useState } from 'react'
import type { Incident, IncidentStatus } from '@/types'
import { useIncidents } from '@/hooks/useIncidents'
import { severityColor, formatRelative, formatTime, cx } from '@/utils/format'
import { IconCheck, IconClock, IconMemory, IconChevronDown } from './icons'

const STATUS_STYLES: Record<IncidentStatus, { label: string; className: string }> = {
  detected: { label: 'Detected', className: 'text-signal-detective bg-signal-detective/10' },
  diagnosing: { label: 'Diagnosing', className: 'text-signal-diagnostician bg-signal-diagnostician/10' },
  diagnosed: { label: 'Diagnosed', className: 'text-signal-diagnostician bg-signal-diagnostician/10' },
  awaiting_approval: { label: 'Awaiting approval', className: 'text-signal-danger bg-signal-danger/10' },
  remediating: { label: 'Remediating', className: 'text-signal-reporter bg-signal-reporter/10' },
  resolved: { label: 'Resolved', className: 'text-signal-remediation bg-signal-remediation/10' },
  auto_resolved: { label: 'Auto-resolved', className: 'text-signal-remediation bg-signal-remediation/10' },
  rejected: { label: 'Rejected', className: 'text-bone-500 bg-graphite-700' },
}

function IncidentRow({ incident }: { incident: Incident }) {
  const [open, setOpen] = useState(false)
  const status = STATUS_STYLES[incident.status]

  return (
    <div className="rounded-lg border border-graphite-700 bg-graphite-900">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full flex-wrap items-center gap-3 px-4 py-3.5 text-left"
      >
        <span className={cx('rounded border px-1.5 py-0.5 font-mono-data text-[10px] uppercase', severityColor[incident.severity])}>
          {incident.severity}
        </span>
        <span className="min-w-0 flex-1 text-[13.5px] font-medium text-bone-100">{incident.title}</span>
        {incident.isAutoResolved && (
          <span className="flex items-center gap-1 rounded bg-signal-diagnostician/10 px-1.5 py-0.5 font-mono-data text-[10px] text-signal-diagnostician">
            <IconMemory className="h-3 w-3" /> auto
          </span>
        )}
        <span className={cx('rounded px-2 py-0.5 font-mono-data text-[10.5px]', status.className)}>
          {status.label}
        </span>
        <span className="flex items-center gap-1 font-mono-data text-[11px] text-bone-500">
          <IconClock className="h-3 w-3" /> {formatRelative(incident.detectedAt)}
        </span>
        <IconChevronDown className={cx('h-4 w-4 text-bone-500 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="border-t border-graphite-700 px-4 py-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500">Service / Server</p>
              <p className="mt-1 text-[13px] text-bone-300">{incident.service} · {incident.server}</p>

              <p className="mt-3 font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500">Detected</p>
              <p className="mt-1 font-mono-data text-[13px] text-bone-300">{formatTime(incident.detectedAt)}</p>

              {incident.resolvedAt && (
                <>
                  <p className="mt-3 font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500">Resolved</p>
                  <p className="mt-1 font-mono-data text-[13px] text-bone-300">{formatTime(incident.resolvedAt)}</p>
                </>
              )}

              {incident.metrics.downtimeMinutes !== undefined && (
                <>
                  <p className="mt-3 font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500">Downtime</p>
                  <p className="mt-1 flex items-center gap-1.5 text-[13px] text-bone-300">
                    {incident.metrics.downtimeMinutes === 0 ? (
                      <span className="flex items-center gap-1 text-signal-remediation">
                        <IconCheck className="h-3.5 w-3.5" /> Zero downtime
                      </span>
                    ) : (
                      `${incident.metrics.downtimeMinutes} minutes`
                    )}
                  </p>
                </>
              )}
            </div>
            <div>
              {incident.rootCause && (
                <>
                  <p className="font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500">Root cause</p>
                  <p className="mt-1 text-[13px] leading-relaxed text-bone-300">{incident.rootCause}</p>
                </>
              )}
              {incident.remediationSteps.length > 0 && (
                <>
                  <p className="mt-3 font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500">Fix applied</p>
                  <ul className="mt-1 space-y-1">
                    {incident.remediationSteps.map((s) => (
                      <li key={s.id} className="text-[13px] text-bone-300">
                        {s.order}. {s.description}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export function IncidentsPage() {
  const { incidents, loading } = useIncidents()
  const [filter, setFilter] = useState<'all' | 'active' | 'resolved'>('all')

  const filtered = incidents.filter((i) => {
    if (filter === 'active') return !['resolved', 'auto_resolved', 'rejected'].includes(i.status)
    if (filter === 'resolved') return ['resolved', 'auto_resolved'].includes(i.status)
    return true
  })

  return (
    <div className="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-[20px] font-semibold text-bone-100">Incidents</h1>
        <div className="flex gap-1 rounded-md border border-graphite-700 p-0.5">
          {(['all', 'active', 'resolved'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cx(
                'rounded px-3 py-1.5 text-[12.5px] font-medium capitalize transition-colors',
                filter === f ? 'bg-graphite-700 text-bone-100' : 'text-bone-500'
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="text-[13px] text-bone-500">Loading incidents…</p>
      ) : filtered.length === 0 ? (
        <p className="rounded-lg border border-dashed border-graphite-600 px-4 py-8 text-center text-[13px] text-bone-500">
          No incidents match this filter.
        </p>
      ) : (
        <div className="space-y-2.5">
          {filtered.map((incident) => (
            <IncidentRow key={incident.id} incident={incident} />
          ))}
        </div>
      )}
    </div>
  )
}
