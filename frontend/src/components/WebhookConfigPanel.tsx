import { useEffect, useState } from 'react'
import { api } from '@/services/api'
import { IconCheck } from './icons'

export function WebhookConfigPanel() {
  const [slackUrl, setSlackUrl] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle')

  useEffect(() => {
    async function loadConfig() {
      try {
        const config = await api.getWebhookConfig()
        setSlackUrl(config.slack_webhook_url || '')
      } catch (err) {
        console.error('Failed to load webhook config', err)
      }
    }
    loadConfig()
  }, [])

  async function handleSave() {
    setIsSaving(true)
    setSaveStatus('idle')
    try {
      await api.setWebhookConfig(slackUrl.trim())
      setSaveStatus('success')
      setTimeout(() => setSaveStatus('idle'), 3000)
    } catch (err) {
      setSaveStatus('error')
    } finally {
      setIsSaving(false)
    }
  }

  const inboundUrl = 'https://aegis-flax-nine.vercel.app/api/webhook/incident'

  return (
    <section className="mt-6 rounded-2xl border border-graphite-700 bg-graphite-900 p-5">
      <div className="flex items-center gap-2">
        <svg className="h-4.5 w-4.5 text-signal-reporter" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        <h2 className="font-mono-data text-[11px] uppercase tracking-widest text-bone-500">Connections & Webhooks</h2>
      </div>
      <p className="mt-1 text-[13px] text-bone-400">
        Manage how Aegis communicates with external services.
      </p>

      <div className="mt-5 grid gap-6 md:grid-cols-2">
        <div className="rounded-xl border border-graphite-700 bg-graphite-950 p-4">
          <p className="text-[13.5px] font-medium text-bone-100">Inbound Webhook</p>
          <p className="mt-1 text-[12.5px] text-bone-500">
            Paste this URL into Datadog, CloudWatch, or your monitoring tool to trigger Aegis.
          </p>
          <div className="mt-3 flex items-center gap-2">
            <input
              type="text"
              readOnly
              value={inboundUrl}
              className="w-full rounded-md border border-graphite-600 bg-graphite-900 px-3 py-2 text-[12px] text-bone-300 outline-none"
            />
            <button
              onClick={() => {
                navigator.clipboard.writeText(inboundUrl)
                alert('Copied to clipboard!')
              }}
              className="flex-shrink-0 rounded-md border border-graphite-600 px-3 py-2 text-[12px] font-medium text-bone-300 hover:bg-graphite-800 transition-colors"
            >
              Copy
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-graphite-700 bg-graphite-950 p-4">
          <p className="text-[13.5px] font-medium text-bone-100">Outbound Webhook (Slack)</p>
          <p className="mt-1 text-[12.5px] text-bone-500">
            Provide a Slack Incoming Webhook URL to receive incident reports in your channel.
          </p>
          <div className="mt-3 flex flex-col gap-3">
            <input
              type="url"
              placeholder="https://hooks.slack.com/services/..."
              value={slackUrl}
              onChange={(e) => setSlackUrl(e.target.value)}
              className="w-full rounded-md border border-graphite-600 bg-graphite-900 px-3 py-2 text-[12px] text-bone-100 placeholder:text-bone-600 outline-none focus:border-signal-reporter"
            />
            <div className="flex items-center gap-3">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="rounded-md bg-signal-reporter px-4 py-1.5 text-[12px] font-semibold text-graphite-950 disabled:opacity-50 transition-opacity hover:opacity-90"
              >
                {isSaving ? 'Saving...' : 'Save Configuration'}
              </button>
              {saveStatus === 'success' && (
                <span className="flex items-center gap-1.5 text-[12px] font-medium text-signal-remediation">
                  <IconCheck className="h-3.5 w-3.5" /> Saved
                </span>
              )}
              {saveStatus === 'error' && (
                <span className="text-[12px] font-medium text-signal-danger">Failed to save</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
