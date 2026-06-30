import { useEffect } from 'react'
import { useAdminOverview } from '@/hooks/useLiveData'
import { useAuthSession } from '@/hooks/useAuthSession'
import { cx, formatRelative } from '@/utils/format'
import { IconAlertTriangle, IconCheck, IconClock, IconLock, IconServer, IconShield } from './icons'

function StatCard({
  label,
  value,
  detail,
  tone = 'text-bone-100',
}: {
  label: string
  value: string | number
  detail: string
  tone?: string
}) {
  return (
    <div className="rounded-xl border border-graphite-700 bg-graphite-900 p-4">
      <p className="font-mono-data text-[10.5px] uppercase tracking-widest text-bone-500">{label}</p>
      <p className={cx('mt-2 text-[22px] font-semibold tracking-tight', tone)}>{value}</p>
      <p className="mt-1 text-[12.5px] text-bone-500">{detail}</p>
    </div>
  )
}

function StatusChip({ status }: { status: string }) {
  const tone =
    status.toLowerCase().includes('warn') || status.toLowerCase().includes('need')
      ? 'bg-signal-amber/10 text-signal-amber'
      : status.toLowerCase().includes('error') || status.toLowerCase().includes('degrad')
        ? 'bg-signal-danger/10 text-signal-danger'
        : 'bg-signal-remediation/10 text-signal-remediation'

  return <span className={cx('rounded-full px-2.5 py-1 font-mono-data text-[10.5px] uppercase tracking-widest', tone)}>{status}</span>
}

export function AdminPage() {
  const { adminOverview, isLive, loading, accessDenied, refresh } = useAdminOverview()
  const { token } = useAuthSession()

  useEffect(() => {
    document.title = 'Aegis Admin'
  }, [])

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <p className="text-[13.5px] text-bone-500">Loading admin overview…</p>
      </div>
    )
  }

  if (accessDenied) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
        <div className="rounded-2xl border border-graphite-700 bg-graphite-900 p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-signal-danger/10 text-signal-danger">
              <IconLock className="h-5 w-5" />
            </div>
            <div>
              <h1 className="font-display text-[24px] font-semibold text-bone-100">Admin access required</h1>
              <p className="mt-1 text-[13.5px] text-bone-400">
                The backend is protecting this area. Add an admin token in Settings to view the live control panel.
              </p>
            </div>
          </div>
          <div className="mt-5 rounded-xl border border-graphite-700 bg-graphite-950 p-4 text-[13px] text-bone-400">
            <p>
              Current token status: {token ? `loaded (${token.length} chars)` : 'none'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-signal-detective/30 bg-signal-detective/10 px-2.5 py-1 font-mono-data text-[10.5px] uppercase tracking-widest text-signal-detective">
              Admin
            </span>
            <StatusChip status={adminOverview.backendStatus} />
            <StatusChip status={adminOverview.authMode} />
          </div>
          <h1 className="font-display text-[26px] font-semibold tracking-tight text-bone-100">Admin Control Center</h1>
          <p className="max-w-2xl text-[13.5px] text-bone-400">
            Live backend summary, service readiness, and deployment posture for the Aegis gateway.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={refresh}
            className="rounded-md border border-graphite-600 px-3.5 py-2 text-[13px] text-bone-300 hover:bg-graphite-800"
          >
            Refresh
          </button>
          <a
            href={adminOverview.docsUrl}
            target="_blank"
            rel="noreferrer"
            className="rounded-md bg-signal-remediation px-3.5 py-2 text-[13px] font-semibold text-graphite-950"
          >
            Open Swagger
          </a>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Environment"
          value={adminOverview.environment}
          detail={`${adminOverview.apiPrefix} · ${adminOverview.authEnabled ? 'protected' : 'open demo'}`}
          tone="text-signal-detective"
        />
        <StatCard
          label="Active incidents"
          value={adminOverview.activeIncidentCount}
          detail={`${adminOverview.pendingApprovals} pending approval`}
          tone="text-signal-amber"
        />
        <StatCard
          label="Knowledge base"
          value={adminOverview.memoryRecordCount}
          detail={`${adminOverview.reportCount} reports generated`}
          tone="text-signal-reporter"
        />
        <StatCard
          label="Monitored servers"
          value={adminOverview.monitoredServers.length || 0}
          detail={`${adminOverview.agentCount} agents in the pipeline`}
          tone="text-signal-remediation"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.35fr_0.9fr]">
        <section className="rounded-2xl border border-graphite-700 bg-graphite-900 p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="font-mono-data text-[11px] uppercase tracking-widest text-bone-500">Service matrix</h2>
              <p className="mt-1 text-[13px] text-bone-400">
                Backend services and infrastructure readiness for this session.
              </p>
            </div>
            <span className="flex items-center gap-1.5 font-mono-data text-[11px] text-bone-500">
              <IconClock className="h-3.5 w-3.5" />
              {formatRelative(adminOverview.startupCheckedAt)}
            </span>
          </div>

          <div className="mt-4 space-y-3">
            {adminOverview.serviceMatrix.map((service) => (
              <div key={service.name} className="flex items-start justify-between gap-4 rounded-xl border border-graphite-700 bg-graphite-950 px-4 py-3">
                <div>
                  <p className="text-[13.5px] font-medium text-bone-100">{service.name}</p>
                  <p className="mt-0.5 text-[12.5px] text-bone-500">{service.detail}</p>
                </div>
                <StatusChip status={service.status} />
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-graphite-700 bg-graphite-900 p-5">
          <div className="flex items-center gap-2">
            <IconShield className="h-4.5 w-4.5 text-signal-detective" />
            <h2 className="font-mono-data text-[11px] uppercase tracking-widest text-bone-500">Recent signals</h2>
          </div>
          <div className="mt-4 space-y-3">
            {adminOverview.recentSignals.map((signal) => (
              <div key={signal} className="rounded-xl border border-graphite-700 bg-graphite-950 px-4 py-3">
                <p className="text-[13.5px] text-bone-100">{signal}</p>
              </div>
            ))}
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-graphite-700 bg-graphite-950 p-3">
              <p className="font-mono-data text-[10.5px] uppercase tracking-widest text-bone-500">Startup</p>
              <p className="mt-2 flex items-center gap-2 text-[13px] text-bone-100">
                {adminOverview.startupOk ? <IconCheck className="h-4 w-4 text-signal-remediation" /> : <IconAlertTriangle className="h-4 w-4 text-signal-danger" />}
                {adminOverview.startupOk ? 'Healthy' : 'Needs attention'}
              </p>
            </div>
            <div className="rounded-xl border border-graphite-700 bg-graphite-950 p-3">
              <p className="font-mono-data text-[10.5px] uppercase tracking-widest text-bone-500">Config</p>
              <p className="mt-2 text-[13px] text-bone-100">
                {adminOverview.qwenConfigured ? 'Qwen configured' : 'Demo mode'}
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
