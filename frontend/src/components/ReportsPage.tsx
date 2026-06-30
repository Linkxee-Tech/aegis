import { useState } from 'react'
import type { IncidentReport } from '@/types'
import { useReports } from '@/hooks/useReports'
import { cx, formatTime, formatRelative } from '@/utils/format'
import { IconClock, IconCheck, IconChevronDown, IconDownload } from './icons'
import { api, ApiError } from '@/services/api'

function ReportCard({ report, isLive }: { report: IncidentReport; isLive: boolean }) {
  const [open, setOpen] = useState(false)
  const [downloadLoading, setDownloadLoading] = useState(false)
  const [ossUrl, setOssUrl] = useState<string | null>(null)

  async function handleDownload() {
    if (!isLive) {
      alert('Download is only available when connected to the live backend. This is currently running in demo mode.')
      return
    }

    setDownloadLoading(true)
    try {
      const { blob, filename, ossUrl: uploadedUrl } = await api.fetchReportDownload(report.id)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = filename
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(url)
      setOssUrl(uploadedUrl)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        alert('Report download requires a valid token in Settings.')
        return
      }
      if (error instanceof ApiError && error.status === 403) {
        alert('Your token is not allowed to download reports.')
        return
      }
      alert('Report download failed.')
    } finally {
      setDownloadLoading(false)
    }
  }

  return (
    <div className="overflow-hidden rounded-lg border border-graphite-700 bg-graphite-900">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full flex-wrap items-center gap-4 px-5 py-4 text-left transition-colors hover:bg-graphite-800/50"
      >
        <span
          className={cx(
            'rounded px-2 py-0.5 font-mono-data text-[10.5px] uppercase tracking-wider',
            report.status === 'final' ? 'bg-signal-reporter/10 text-signal-reporter' : 'bg-bone-800 text-bone-400'
          )}
        >
          {report.status}
        </span>

        <div className="min-w-0 flex-1">
          <h3 className="truncate text-[14.5px] font-medium text-bone-100">{report.title}</h3>
          <p className="mt-1 line-clamp-1 text-[13px] text-bone-400">{report.summary}</p>
        </div>

        <div className="flex items-center gap-4 text-bone-500">
          <span className="flex items-center gap-1.5 font-mono-data text-[12px]">
            <IconClock className="h-3.5 w-3.5" />
            {formatRelative(report.generatedAt)}
          </span>
          <IconChevronDown className={cx('h-4 w-4 transition-transform', open && 'rotate-180')} />
        </div>
      </button>

      {open && (
        <div className="border-t border-graphite-700 bg-graphite-900/50 px-5 py-5">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-5">
              <div>
                <h4 className="mb-2 font-mono-data text-[11px] uppercase tracking-widest text-bone-500">
                  Root Cause Analysis
                </h4>
                <p className="whitespace-pre-wrap text-[13.5px] leading-relaxed text-bone-300">
                  {report.rootCauseAnalysis}
                </p>
              </div>

              <div>
                <h4 className="mb-2 font-mono-data text-[11px] uppercase tracking-widest text-bone-500">
                  Actions Taken
                </h4>
                <ul className="list-inside list-disc space-y-1">
                  {report.actionsTaken.map((action, i) => (
                    <li key={i} className="text-[13.5px] text-bone-300">
                      {action}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="space-y-5 md:border-l md:border-graphite-700 md:pl-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="mb-1 font-mono-data text-[11px] uppercase tracking-widest text-bone-500">
                    Generated
                  </h4>
                  <p className="font-mono-data text-[13px] text-bone-300">{formatTime(report.generatedAt)}</p>
                </div>
                <div>
                  <h4 className="mb-1 font-mono-data text-[11px] uppercase tracking-widest text-bone-500">
                    Downtime
                  </h4>
                  <p className="flex items-center gap-1.5 text-[13px] text-bone-300">
                    {report.downtimeMinutes === 0 ? (
                      <span className="flex items-center gap-1 text-signal-remediation">
                        <IconCheck className="h-3.5 w-3.5" /> Zero
                      </span>
                    ) : (
                      `${report.downtimeMinutes} mins`
                    )}
                  </p>
                </div>
                {report.costImpactEstimate && (
                  <div className="col-span-2">
                    <h4 className="mb-1 font-mono-data text-[11px] uppercase tracking-widest text-bone-500">
                      Cost Impact
                    </h4>
                    <p className="font-mono-data text-[13px] text-signal-danger">{report.costImpactEstimate}</p>
                  </div>
                )}
              </div>

              <div className="mt-4 border-t border-graphite-700 pt-4">
                <button
                  onClick={handleDownload}
                  disabled={downloadLoading}
                  className={cx(
                    'inline-flex items-center justify-center rounded px-4 py-2 text-[13px] font-medium transition-colors',
                    downloadLoading ? 'cursor-not-allowed bg-bone-300 text-graphite-900 opacity-70' : 'bg-bone-100 text-graphite-900 hover:bg-bone-300'
                  )}
                >
                  {downloadLoading ? 'Preparing PDF…' : 'Download PDF'}
                </button>

                {ossUrl && (
                  <a
                    href={ossUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-3 flex items-center gap-1.5 text-[12.5px] text-signal-detective hover:text-bone-100"
                  >
                    <IconDownload className="h-3.5 w-3.5" />
                    Open OSS copy
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export function ReportsPage() {
  const { reports, isLive, loading } = useReports()

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-[24px] font-semibold tracking-tight text-bone-100">Incident Reports</h1>
          <p className="mt-1 text-[13.5px] text-bone-400">
            Post-mortem documentation and analysis generated by the Reporter agent.
          </p>
        </div>
      </div>

      {loading ? (
        <p className="text-[13.5px] text-bone-500">Loading reports…</p>
      ) : reports.length === 0 ? (
        <div className="rounded-xl border border-dashed border-graphite-600 px-4 py-12 text-center">
          <p className="text-[14px] text-bone-500">No reports have been generated yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <ReportCard key={report.id} report={report} isLive={isLive} />
          ))}
        </div>
      )}
    </div>
  )
}
