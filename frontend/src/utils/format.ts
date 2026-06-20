export function formatTime(iso: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

export function formatRelative(iso: string): string {
  if (!iso) return '—'
  const diffMs = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ')
}

export const severityColor: Record<string, string> = {
  critical: 'text-signal-danger border-signal-danger/40 bg-signal-danger/10',
  warning: 'text-signal-reporter border-signal-reporter/40 bg-signal-reporter/10',
  info: 'text-signal-detective border-signal-detective/40 bg-signal-detective/10',
}

export const agentColorMap: Record<string, { text: string; border: string; bg: string; ring: string }> = {
  detective: { text: 'text-signal-detective', border: 'border-signal-detective/40', bg: 'bg-signal-detective/10', ring: 'ring-signal-detective/30' },
  diagnostician: { text: 'text-signal-diagnostician', border: 'border-signal-diagnostician/40', bg: 'bg-signal-diagnostician/10', ring: 'ring-signal-diagnostician/30' },
  remediation: { text: 'text-signal-remediation', border: 'border-signal-remediation/40', bg: 'bg-signal-remediation/10', ring: 'ring-signal-remediation/30' },
  reporter: { text: 'text-signal-reporter', border: 'border-signal-reporter/40', bg: 'bg-signal-reporter/10', ring: 'ring-signal-reporter/30' },
  memory: { text: 'text-signal-diagnostician', border: 'border-signal-diagnostician/40', bg: 'bg-signal-diagnostician/10', ring: 'ring-signal-diagnostician/30' },
}
