import type { Incident, TimelineEvent } from '@/types'
import { IconDetective, IconDiagnostician, IconRemediation, IconReporter } from './icons'
import { agentColorMap, cx, formatTime } from '@/utils/format'

const AGENT_ICONS = {
  detective: IconDetective,
  diagnostician: IconDiagnostician,
  remediation: IconRemediation,
  reporter: IconReporter,
  memory: IconDetective,
}

function TimelineRow({ event, isLast }: { event: TimelineEvent; isLast: boolean }) {
  const Icon = AGENT_ICONS[event.agentId]
  const colors = agentColorMap[event.agentId] ?? agentColorMap.detective

  return (
    <div className="flex gap-3.5">
      <div className="flex flex-col items-center">
        <div
          className={cx(
            'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border',
            event.status === 'pending' ? 'border-graphite-600 bg-graphite-800' : colors.border,
            event.status !== 'pending' && colors.bg
          )}
        >
          <Icon className={cx('h-4 w-4', event.status === 'pending' ? 'text-bone-500' : colors.text)} />
        </div>
        {!isLast && <div className="my-1 w-px flex-1 bg-graphite-700" />}
      </div>
      <div className={cx('flex-1 pb-5', event.status === 'pending' && 'opacity-50')}>
        <div className="flex items-center justify-between gap-2">
          <p className="text-[13.5px] font-medium text-bone-100">{event.title}</p>
          {event.timestamp && (
            <span className="font-mono-data text-[11px] text-bone-500">{formatTime(event.timestamp)}</span>
          )}
        </div>
        <p className="mt-0.5 text-[12.5px] leading-relaxed text-bone-500">{event.detail}</p>
        {event.status === 'in_progress' && (
          <span className="mt-1.5 inline-flex items-center gap-1.5 font-mono-data text-[10.5px] uppercase tracking-wide text-signal-amber">
            <span className="h-1 w-1 animate-blink rounded-full bg-signal-amber" />
            In progress
          </span>
        )}
      </div>
    </div>
  )
}

export function IncidentTimeline({ incident }: { incident: Incident }) {
  return (
    <div>
      {incident.timeline.map((event, i) => (
        <TimelineRow key={event.id} event={event} isLast={i === incident.timeline.length - 1} />
      ))}
    </div>
  )
}
