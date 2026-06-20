import { useState } from 'react'
import type { Incident } from '@/types'
import { IconLock, IconCheck, IconX, IconAlertTriangle } from './icons'
import { cx } from '@/utils/format'

interface ApprovalGateProps {
  incident: Incident
  onApprove: () => void
  onReject: (reason: string) => void
}

const RISK_STYLES: Record<string, string> = {
  low: 'text-signal-remediation bg-signal-remediation/10 border-signal-remediation/30',
  medium: 'text-signal-reporter bg-signal-reporter/10 border-signal-reporter/30',
  high: 'text-signal-danger bg-signal-danger/10 border-signal-danger/30',
}

export function ApprovalGate({ incident, onApprove, onReject }: ApprovalGateProps) {
  const [armed, setArmed] = useState(false)
  const [showReject, setShowReject] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  return (
    <div className="rounded-lg border border-signal-danger/30 bg-graphite-900">
      <div className="flex items-center gap-2.5 border-b border-graphite-700 px-5 py-3.5">
        <IconLock className="h-4 w-4 text-signal-danger" locked={!armed} />
        <span className="text-[13.5px] font-semibold text-bone-100">Human approval checkpoint</span>
        <span className="ml-auto font-mono-data text-[11px] text-bone-500">
          No live action runs without sign-off
        </span>
      </div>

      <div className="px-5 py-4">
        <p className="text-[13px] text-bone-500">
          Remediation Agent proposes the following plan for{' '}
          <span className="font-mono-data text-bone-300">{incident.server}</span>:
        </p>

        <ol className="mt-3 space-y-2">
          {incident.remediationSteps.map((step) => (
            <li
              key={step.id}
              className="flex items-start gap-3 rounded-md border border-graphite-700 bg-graphite-800 px-3.5 py-3"
            >
              <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-graphite-700 font-mono-data text-[11px] text-bone-300">
                {step.order}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[13px] text-bone-100">{step.description}</p>
                  <span
                    className={cx(
                      'flex-shrink-0 rounded border px-1.5 py-0.5 font-mono-data text-[10px] uppercase',
                      RISK_STYLES[step.riskLevel]
                    )}
                  >
                    {step.riskLevel}
                  </span>
                </div>
                {step.command && (
                  <code className="mt-1.5 block overflow-x-auto rounded bg-graphite-950 px-2.5 py-1.5 font-mono-data text-[11px] text-bone-500">
                    {step.command}
                  </code>
                )}
              </div>
            </li>
          ))}
        </ol>

        {!showReject ? (
          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={() => {
                if (!armed) {
                  setArmed(true)
                } else {
                  onApprove()
                }
              }}
              className={cx(
                'flex flex-1 items-center justify-center gap-2 rounded-md border px-4 py-3 text-[13.5px] font-semibold transition-all',
                armed
                  ? 'border-signal-danger bg-signal-danger text-graphite-950 shadow-[0_0_24px_rgba(255,92,92,0.35)]'
                  : 'border-graphite-600 bg-graphite-800 text-bone-100 hover:border-bone-500'
              )}
            >
              <IconLock className="h-4 w-4" locked={!armed} />
              {armed ? 'Confirm — execute on live server' : 'Arm approval'}
            </button>
            {armed && (
              <button
                onClick={() => setArmed(false)}
                className="rounded-md border border-graphite-600 px-3.5 py-3 text-[13px] text-bone-500 hover:text-bone-300"
              >
                Cancel
              </button>
            )}
            {!armed && (
              <button
                onClick={() => setShowReject(true)}
                className="flex items-center gap-1.5 rounded-md border border-graphite-600 px-4 py-3 text-[13.5px] font-medium text-bone-300 hover:border-signal-danger/40 hover:text-signal-danger"
              >
                <IconX className="h-3.5 w-3.5" />
                Reject
              </button>
            )}
          </div>
        ) : (
          <div className="mt-4 space-y-2.5 rounded-md border border-graphite-700 bg-graphite-800 p-3.5">
            <div className="flex items-center gap-2 text-[12.5px] text-bone-500">
              <IconAlertTriangle className="h-3.5 w-3.5 text-signal-reporter" />
              Tell the Diagnostician what to reconsider (optional)
            </div>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Don't roll back — the leak is in the cache layer, not the deploy"
              rows={2}
              className="w-full resize-none rounded-md border border-graphite-600 bg-graphite-950 px-3 py-2 text-[13px] text-bone-100 placeholder:text-bone-500/60 focus:border-signal-detective"
            />
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  onReject(rejectReason)
                  setShowReject(false)
                }}
                className="rounded-md bg-signal-danger px-3.5 py-2 text-[13px] font-semibold text-graphite-950"
              >
                Confirm reject
              </button>
              <button
                onClick={() => setShowReject(false)}
                className="rounded-md border border-graphite-600 px-3.5 py-2 text-[13px] text-bone-500"
              >
                Back
              </button>
            </div>
          </div>
        )}

        {armed && !showReject && (
          <p className="mt-2.5 flex items-center gap-1.5 text-[11.5px] text-signal-danger">
            <IconCheck className="h-3 w-3" />
            Approval armed — confirming will run these commands on a live server.
          </p>
        )}
      </div>
    </div>
  )
}
