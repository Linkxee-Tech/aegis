import type { Incident } from '@/types'
import { formatTime } from '@/utils/format'

interface HistoryTimelineProps {
  incidents: Incident[]
}

const SEVERITY_DOT: Record<string, string> = {
  critical: 'bg-signal-danger',
  warning: 'bg-signal-reporter',
  info: 'bg-signal-detective',
}

export function HistoryTimeline({ incidents }: HistoryTimelineProps) {
  const now = Date.now()
  const windowMs = 26 * 60 * 60 * 1000
  const start = now - windowMs

  const hourMarks = Array.from({ length: 8 }, (_, i) => {
    const t = new Date(start + (i / 7) * windowMs)
    return t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
  })

  return (
    <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-[14px] font-semibold text-bone-100">Incident timeline</h3>
        <span className="font-mono-data text-[11px] text-bone-500">Last 26 hours</span>
      </div>

      <div className="relative mt-7 h-10">
        <div className="absolute left-0 right-0 top-1/2 h-px bg-graphite-700" />
        {incidents.map((incident) => {
          const t = new Date(incident.detectedAt).getTime()
          const pct = Math.min(100, Math.max(0, ((t - start) / windowMs) * 100))
          return (
            <div
              key={incident.id}
              className="group absolute top-1/2 -translate-x-1/2 -translate-y-1/2 cursor-default"
              style={{ left: `${pct}%` }}
            >
              <div
                className={`h-3 w-3 rounded-full ring-4 ring-graphite-900 ${SEVERITY_DOT[incident.severity]}`}
              />
              <div className="pointer-events-none absolute bottom-5 left-1/2 z-10 w-56 -translate-x-1/2 rounded-md border border-graphite-600 bg-graphite-800 p-2.5 opacity-0 shadow-xl transition-opacity group-hover:opacity-100">
                <p className="text-[11.5px] font-medium text-bone-100">{incident.title}</p>
                <p className="mt-0.5 font-mono-data text-[10.5px] text-bone-500">
                  {formatTime(incident.detectedAt)} · {incident.status.replace('_', ' ')}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-2 flex justify-between font-mono-data text-[10.5px] text-bone-500">
        {hourMarks.map((h, i) => (
          <span key={i}>{h}</span>
        ))}
      </div>
    </div>
  )
}
