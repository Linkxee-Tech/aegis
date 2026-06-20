import { useState } from 'react'
import type { Incident } from '@/types'
import { IncidentTimeline } from './IncidentTimeline'
import { ApprovalGate } from './ApprovalModal'
import { IconAlertTriangle, IconServer, IconClock, IconChevronDown } from './icons'
import { severityColor, formatRelative, cx } from '@/utils/format'

interface ActiveIncidentPanelProps {
  incident: Incident
  onApprove: () => void
  onReject: (reason: string) => void
}

function ThinkingIndicator({ label }: { label: string }) {
  return (
    <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-signal-diagnostician/30 bg-signal-diagnostician/10 px-3 py-1.5 text-[11px] text-signal-diagnostician">
      <span className="flex items-center gap-1">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current [animation-delay:-0.2s]" />
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current [animation-delay:0s]" />
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current [animation-delay:0.2s]" />
      </span>
      <span>{label}</span>
    </div>
  )
}

export function ActiveIncidentPanel({ incident, onApprove, onReject }: ActiveIncidentPanelProps) {
  const [evidenceOpen, setEvidenceOpen] = useState(true)

  return (
    <div className="rounded-lg border border-graphite-700 bg-graphite-900">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-graphite-700 px-5 py-4">
        <div className="flex items-start gap-3">
          <span
            className={cx(
              'mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md border',
              severityColor[incident.severity]
            )}
          >
            <IconAlertTriangle className="h-4 w-4" />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-display text-[15.5px] font-semibold text-bone-100">{incident.title}</h2>
              <span className="font-mono-data text-[10.5px] text-bone-500">{incident.id}</span>
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-3 font-mono-data text-[11.5px] text-bone-500">
              <span className="flex items-center gap-1">
                <IconServer className="h-3 w-3" /> {incident.server}
              </span>
              <span className="flex items-center gap-1">
                <IconClock className="h-3 w-3" /> {formatRelative(incident.detectedAt)}
              </span>
            </div>
          </div>
        </div>
        <span
          className={cx(
            'rounded-md border px-2.5 py-1 font-mono-data text-[11px] uppercase tracking-wide',
            severityColor[incident.severity]
          )}
        >
          {incident.severity}
        </span>
      </div>

      <div className="grid gap-5 p-5 lg:grid-cols-[1.1fr_1fr]">
        <div>
          <IncidentTimeline incident={incident} />

          {incident.rootCause && (
            <div className="mt-1 rounded-md border border-graphite-700 bg-graphite-800 p-3.5">
              <p className="font-mono-data text-[10.5px] uppercase tracking-wide text-signal-diagnostician">
                Root cause
              </p>
              <p className="mt-1.5 text-[13px] leading-relaxed text-bone-300">{incident.rootCause}</p>
            </div>
          )}

          {incident.status === 'diagnosing' && <ThinkingIndicator label="Diagnostician is typing the root cause" />}
          {incident.status === 'awaiting_approval' && <ThinkingIndicator label="Remediation is waiting for approval" />}

          <button
            onClick={() => setEvidenceOpen(!evidenceOpen)}
            className="mt-3 flex w-full items-center justify-between rounded-md border border-graphite-700 px-3.5 py-2.5 text-left"
          >
            <span className="text-[12.5px] font-medium text-bone-300">
              Evidence ({incident.evidence.length})
            </span>
            <IconChevronDown
              className={cx('h-4 w-4 text-bone-500 transition-transform', evidenceOpen && 'rotate-180')}
            />
          </button>
          {evidenceOpen && (
            <ul className="mt-2 space-y-1.5 px-1">
              {incident.evidence.map((e, i) => (
                <li key={i} className="flex gap-2 text-[12.5px] text-bone-500">
                  <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-bone-500" />
                  {e}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <ApprovalGate incident={incident} onApprove={onApprove} onReject={onReject} />
        </div>
      </div>
    </div>
  )
}
