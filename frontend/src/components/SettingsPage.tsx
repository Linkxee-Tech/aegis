import { useEffect, useState } from 'react'
import { useAuthSession } from '@/hooks/useAuthSession'
import { cx } from '@/utils/format'

function Toggle({ enabled, onChange }: { enabled: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={cx(
        'relative h-5 w-9 rounded-full transition-colors',
        enabled ? 'bg-signal-remediation' : 'bg-graphite-600'
      )}
    >
      <span
        className={cx(
          'absolute top-0.5 h-4 w-4 rounded-full bg-graphite-950 transition-transform',
          enabled ? 'translate-x-[18px]' : 'translate-x-0.5'
        )}
      />
    </button>
  )
}

function SettingRow({
  title,
  description,
  enabled,
  onChange,
}: {
  title: string
  description: string
  enabled: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-graphite-700 py-4 last:border-0">
      <div>
        <p className="text-[13.5px] font-medium text-bone-100">{title}</p>
        <p className="mt-0.5 text-[12.5px] text-bone-500">{description}</p>
      </div>
      <Toggle enabled={enabled} onChange={onChange} />
    </div>
  )
}

export function SettingsPage() {
  const [autoApply, setAutoApply] = useState(true)
  const [requireApprovalHighRisk, setRequireApprovalHighRisk] = useState(true)
  const [notifySlack, setNotifySlack] = useState(true)
  const [confidence, setConfidence] = useState(85)
  const { token, setToken, clearToken } = useAuthSession()
  const [draftToken, setDraftToken] = useState(token)

  useEffect(() => {
    setDraftToken(token)
  }, [token])

  return (
    <div className="mx-auto max-w-3xl space-y-5 px-4 py-6 sm:px-6">
      <div>
        <h1 className="font-display text-[20px] font-semibold text-bone-100">Settings</h1>
        <p className="mt-1 text-[13px] text-bone-500">Configure how much autonomy Aegis has.</p>
      </div>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
        <h2 className="font-mono-data text-[11px] uppercase tracking-wide text-bone-500">Gateway access</h2>
        <p className="mt-2 text-[12.5px] text-bone-500">
          Paste a Bearer/API token here when the backend gateway auth is enabled. Viewer tokens can browse,
          operator tokens can approve, reject, and simulate incidents.
        </p>
        <div className="mt-4 space-y-3">
          <div>
            <label className="text-[13px] font-medium text-bone-100">API token</label>
            <input
              type="password"
              value={draftToken}
              onChange={(e) => setDraftToken(e.target.value)}
              placeholder="Paste viewer/operator/admin token"
              className="mt-2 w-full rounded-md border border-graphite-600 bg-graphite-950 px-3 py-2 text-[13px] text-bone-100 placeholder:text-bone-500/60 focus:border-signal-detective"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setToken(draftToken)}
              className="rounded-md bg-signal-remediation px-3.5 py-2 text-[13px] font-semibold text-graphite-950"
            >
              Save token
            </button>
            <button
              onClick={() => {
                clearToken()
                setDraftToken('')
              }}
              className="rounded-md border border-graphite-600 px-3.5 py-2 text-[13px] text-bone-300"
            >
              Clear token
            </button>
          </div>
          <p className="font-mono-data text-[11px] text-bone-500">
            Current token: {token ? `loaded (${token.length} chars)` : 'none'}
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
        <h2 className="font-mono-data text-[11px] uppercase tracking-wide text-bone-500">Approval rules</h2>
        <div className="mt-2">
          <SettingRow
            title="Auto-apply known fixes"
            description="When the Memory Agent matches a prior incident above the confidence threshold, skip the approval gate."
            enabled={autoApply}
            onChange={setAutoApply}
          />
          <SettingRow
            title="Always require approval for high-risk steps"
            description="Even with a matched memory, any step marked high-risk still needs a human to confirm."
            enabled={requireApprovalHighRisk}
            onChange={setRequireApprovalHighRisk}
          />
          <SettingRow
            title="Notify on-call via Slack"
            description="Post to the on-call channel whenever a new incident is detected or a fix is awaiting approval."
            enabled={notifySlack}
            onChange={setNotifySlack}
          />
        </div>

        <div className="mt-4 pt-1">
          <div className="flex items-center justify-between">
            <p className="text-[13.5px] font-medium text-bone-100">Memory confidence threshold</p>
            <span className="font-mono-data text-[13px] text-signal-amber">{confidence}%</span>
          </div>
          <p className="mt-0.5 text-[12.5px] text-bone-500">
            Minimum similarity score before Aegis trusts a past solution enough to suggest auto-apply.
          </p>
          <input
            type="range"
            min={50}
            max={99}
            value={confidence}
            onChange={(e) => setConfidence(Number(e.target.value))}
            className="mt-3 w-full accent-signal-amber"
          />
        </div>
      </div>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
        <h2 className="font-mono-data text-[11px] uppercase tracking-wide text-bone-500">Connections</h2>
        <div className="mt-3 space-y-2.5">
          {[
            { name: 'Qwen Cloud API', status: 'Connected', model: 'qwen-plus · qwen-flash · qwen-coder' },
            { name: 'Alibaba Cloud ECS', status: 'Connected', model: '4 monitored instances' },
            { name: 'PostgreSQL + pgvector', status: 'Connected', model: 'aegis-memory-db' },
            { name: 'Redis', status: 'Connected', model: 'session cache' },
          ].map((c) => (
            <div
              key={c.name}
              className="flex items-center justify-between rounded-md border border-graphite-700 bg-graphite-800 px-3.5 py-2.5"
            >
              <div>
                <p className="text-[13px] text-bone-100">{c.name}</p>
                <p className="font-mono-data text-[11px] text-bone-500">{c.model}</p>
              </div>
              <span className="flex items-center gap-1.5 font-mono-data text-[11px] text-signal-remediation">
                <span className="h-1.5 w-1.5 rounded-full bg-signal-remediation" />
                {c.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
