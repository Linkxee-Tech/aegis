import { useState } from 'react'
import type { IncidentReport } from '@/types'
import { useReports } from '@/hooks/useLiveData'
import { useToast } from '@/hooks/useToast'
import { api } from '@/services/api'
import { formatTime, cx } from '@/utils/format'
import { IconDownload, IconReporter } from './icons'

function ReportCard({ report, onExport }: { report: IncidentReport; onExport: (report: IncidentReport) => void }) {
  const [showMarkdown, setShowMarkdown] = useState(false)

  return (
    <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md bg-signal-reporter/10">
            <IconReporter className="h-[18px] w-[18px] text-signal-reporter" />
          </div>
          <div>
            <h3 className="font-display text-[14.5px] font-semibold text-bone-100">{report.title}</h3>
            <p className="mt-0.5 font-mono-data text-[11px] text-bone-500">
              {report.incidentId} · generated {formatTime(report.generatedAt)}
            </p>
          </div>
        </div>
        <span
          className={cx(
            'flex-shrink-0 rounded px-2 py-0.5 font-mono-data text-[10.5px] uppercase',
            report.status === 'final' ? 'bg-signal-remediation/10 text-signal-remediation' : 'bg-bone-500/10 text-bone-500'
          )}
        >
          {report.status}
        </span>
      </div>

      <p className="mt-3.5 text-[13px] leading-relaxed text-bone-300">{report.summary}</p>

      <div className="mt-3.5 rounded-md border border-graphite-700 bg-graphite-800 p-3.5">
        <p className="font-mono-data text-[10.5px] uppercase tracking-wide text-signal-diagnostician">
          Root cause analysis
        </p>
        <p className="mt-1.5 text-[12.5px] leading-relaxed text-bone-500">{report.rootCauseAnalysis}</p>
      </div>

      <div className="mt-3.5">
        <p className="font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500">Actions taken</p>
        <ul className="mt-1.5 space-y-1">
          {report.actionsTaken.map((a, i) => (
            <li key={i} className="flex gap-2 text-[12.5px] text-bone-300">
              <span className="font-mono-data text-bone-500">{String(i + 1).padStart(2, '0')}</span>
              {a}
            </li>
          ))}
        </ul>
      </div>

      {report.markdownReport && (
        <div className="mt-3.5">
          <button
            onClick={() => setShowMarkdown(!showMarkdown)}
            className="flex items-center gap-1.5 text-[12px] text-signal-detective hover:text-bone-300"
          >
            <span>{showMarkdown ? '▾' : '▸'}</span>
            {showMarkdown ? 'Hide' : 'View'} full Markdown report
          </button>
          {showMarkdown && (
            <pre className="scrollbar-thin mt-2 max-h-72 overflow-auto rounded-md border border-graphite-700 bg-graphite-950 p-3.5 font-mono-data text-[11px] leading-relaxed text-bone-300 whitespace-pre-wrap">
              {report.markdownReport}
            </pre>
          )}
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-graphite-700 pt-3.5">
        <div className="flex items-center gap-4 font-mono-data text-[12px] text-bone-500">
          <span>
            Downtime <span className="text-bone-100">{report.downtimeMinutes}m</span>
          </span>
          {report.costImpactEstimate && (
            <span className="text-signal-remediation">{report.costImpactEstimate}</span>
          )}
        </div>
        <button
          onClick={() => onExport(report)}
          className="flex items-center gap-1.5 rounded-md border border-graphite-600 px-3 py-1.5 text-[12.5px] font-medium text-bone-300 hover:border-bone-500"
        >
          <IconDownload className="h-3.5 w-3.5" />
          Export PDF
        </button>
      </div>
    </div>
  )
}

export function ReportsPage() {
  const { reports, loading } = useReports()
  const { toast, showToast } = useToast()
  const [statusFilter, setStatusFilter] = useState<'all' | 'final' | 'draft'>('all')

  const filtered = reports.filter((r) => statusFilter === 'all' || r.status === statusFilter)

  async function handleExport(report: IncidentReport) {
    try {
      const url = api.downloadReport(report.id)
      const res = await fetch(url)
      if (!res.ok) throw new Error('not available')
      window.open(url, '_blank')
    } catch {
      showToast('PDF export isn\'t wired up to OSS yet in this build — see docs/architecture.md')
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-[20px] font-semibold text-bone-100">Reports</h1>
          <p className="mt-1 text-[13px] text-bone-500">
            Generated automatically by the Reporter Agent after every incident.
          </p>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as 'all' | 'final' | 'draft')}
          className="rounded-md border border-graphite-600 bg-graphite-800 px-3 py-2 text-[12.5px] text-bone-300"
        >
          <option value="all">All reports</option>
          <option value="final">Final only</option>
          <option value="draft">Drafts</option>
        </select>
      </div>

      {loading ? (
        <p className="text-[13px] text-bone-500">Loading reports…</p>
      ) : filtered.length === 0 ? (
        <p className="rounded-lg border border-dashed border-graphite-600 px-4 py-8 text-center text-[13px] text-bone-500">
          No reports match this filter.
        </p>
      ) : (
        <div className="space-y-4">
          {filtered.map((r) => (
            <ReportCard key={r.id} report={r} onExport={handleExport} />
          ))}
        </div>
      )}

      {toast && (
        <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-md border border-graphite-600 bg-graphite-800 px-4 py-3 text-[13px] text-bone-100 shadow-2xl">
          {toast}
        </div>
      )}
    </div>
  )
}
