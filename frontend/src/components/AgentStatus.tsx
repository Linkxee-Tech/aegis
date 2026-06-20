import type { Agent } from '@/types'
import { IconDetective, IconDiagnostician, IconRemediation, IconReporter } from './icons'
import { agentColorMap, cx } from '@/utils/format'

const AGENT_ICONS = {
  detective: IconDetective,
  diagnostician: IconDiagnostician,
  remediation: IconRemediation,
  reporter: IconReporter,
  memory: IconDetective,
}

const STATUS_LABEL: Record<Agent['status'], string> = {
  active: 'Active',
  idle: 'Idle',
  thinking: 'Analyzing',
  error: 'Error',
  awaiting_approval: 'Awaiting approval',
}

interface AgentStatusCardProps {
  agent: Agent
}

function SignalTrace({ colorVar, isLive }: { colorVar: string; isLive: boolean }) {
  return (
    <svg viewBox="0 0 200 36" className="h-9 w-full" preserveAspectRatio="none">
      <path
        d="M0 18 L30 18 L38 6 L46 30 L54 12 L62 18 L90 18 L98 24 L106 10 L114 18 L200 18"
        fill="none"
        stroke={colorVar}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={isLive ? 'signal-trace' : ''}
        opacity={isLive ? 0.9 : 0.25}
      />
    </svg>
  )
}

export function AgentStatusCard({ agent }: AgentStatusCardProps) {
  const Icon = AGENT_ICONS[agent.id]
  const colors = agentColorMap[agent.color] ?? agentColorMap.detective
  const isLive = agent.status === 'active' || agent.status === 'thinking'
  const colorHex: Record<string, string> = {
    detective: '#4D9FFF',
    diagnostician: '#A87CFF',
    remediation: '#4ADE80',
    reporter: '#FFB454',
  }

  return (
    <div
      className={cx(
        'group relative overflow-hidden rounded-lg border bg-graphite-900 p-4 transition-all',
        colors.border,
        !isLive && 'border-opacity-70',
        agent.status === 'awaiting_approval' && 'ring-1 ring-signal-danger/40'
      )}
    >
      <div className="flex items-start justify-between">
        <div className={cx('flex h-9 w-9 items-center justify-center rounded-md', colors.bg)}>
          <Icon className={cx('h-[18px] w-[18px]', colors.text)} />
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={cx(
              'h-1.5 w-1.5 rounded-full',
              agent.status === 'active' && 'animate-pulse-slow bg-signal-remediation',
              agent.status === 'thinking' && 'animate-blink bg-signal-reporter',
              agent.status === 'idle' && 'bg-bone-500',
              agent.status === 'awaiting_approval' && 'animate-blink bg-signal-danger',
              agent.status === 'error' && 'bg-signal-danger'
            )}
          />
          <span className="font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500">
            {STATUS_LABEL[agent.status]}
          </span>
        </div>
      </div>

      <h3 className="mt-3 font-display text-[15px] font-semibold text-bone-100">{agent.name}</h3>
      <p className="mt-0.5 text-[12.5px] leading-snug text-bone-500">{agent.role}</p>

      <div className="mt-3">
        <SignalTrace colorVar={colorHex[agent.color] ?? '#4D9FFF'} isLive={isLive} />
      </div>

      <div className="mt-2 flex items-baseline justify-between border-t border-graphite-700 pt-2.5">
        <span className="font-mono-data text-[11px] text-bone-500">{agent.model}</span>
        <span className="font-mono-data text-[13px] font-semibold text-bone-100">
          {agent.metricValue}
          <span className="ml-1 font-display text-[10.5px] font-normal text-bone-500">{agent.metricLabel}</span>
        </span>
      </div>
    </div>
  )
}

export function AgentStatusGrid({ agents }: { agents: Agent[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {agents.map((agent) => (
        <AgentStatusCard key={agent.id} agent={agent} />
      ))}
    </div>
  )
}
