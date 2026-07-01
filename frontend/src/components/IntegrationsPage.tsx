import { IconCheck } from './icons'

export function IntegrationsPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-6 sm:px-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div>
        <h1 className="font-display text-[20px] font-semibold text-bone-100">Integrations Guide</h1>
        <p className="mt-1 text-[13px] text-bone-500">
          How to connect Aegis to external tools like Slack, Datadog, and Alibaba Cloud.
        </p>
      </div>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
        <h2 className="flex items-center gap-2 font-display text-[15px] font-medium text-bone-100">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-graphite-800 text-[12px] text-bone-300">1</span>
          Inbound Webhook (Receive Alerts)
        </h2>
        <p className="mt-2 text-[13px] text-bone-400">
          Use this when you want external tools like Datadog, AWS CloudWatch, or Prometheus to trigger an Aegis investigation.
        </p>
        <div className="mt-4 rounded-md border border-graphite-700 bg-graphite-950 p-4">
          <p className="text-[12.5px] font-medium text-bone-300">Your Webhook URL</p>
          <code className="mt-2 block rounded bg-graphite-800 px-3 py-2 text-[12px] text-bone-100">
            https://your-aegis-app.onrender.com/api/webhook/incident
          </code>
          <p className="mt-3 text-[12.5px] text-bone-500">
            Paste this URL into your external monitoring tool's webhook configuration. Aegis expects a standard JSON payload.
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
        <h2 className="flex items-center gap-2 font-display text-[15px] font-medium text-bone-100">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-graphite-800 text-[12px] text-bone-300">2</span>
          Outbound Webhook (Send to Slack)
        </h2>
        <p className="mt-2 text-[13px] text-bone-400">
          Use this to receive human-readable alerts in Slack, Microsoft Teams, or Jira when Aegis resolves an incident.
        </p>
        <div className="mt-4 rounded-md border border-graphite-700 bg-graphite-950 p-4">
          <p className="text-[12.5px] font-medium text-bone-300">Slack Configuration</p>
          <ol className="mt-2 list-decimal space-y-1.5 pl-4 text-[12.5px] text-bone-400">
            <li>Go to api.slack.com and create a new Incoming Webhook.</li>
            <li>Copy the generated Webhook URL (starts with <code className="text-bone-300">https://hooks.slack.com/...</code>).</li>
            <li>Add it to your Aegis backend <code className="text-bone-300">.env</code> file.</li>
          </ol>
          <code className="mt-3 block rounded bg-graphite-800 px-3 py-2 text-[12px] text-bone-100">
            SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR_WORKSPACE/YOUR_CHANNEL/YOUR_SECRET
          </code>
        </div>
      </div>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
        <h2 className="flex items-center gap-2 font-display text-[15px] font-medium text-bone-100">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-graphite-800 text-[12px] text-bone-300">3</span>
          Active Polling (Alibaba Cloud)
        </h2>
        <p className="mt-2 text-[13px] text-bone-400">
          Aegis can natively monitor Alibaba Cloud Log Service (SLS) and CloudMonitor without needing external webhooks.
        </p>
        <div className="mt-4 rounded-md border border-graphite-700 bg-graphite-950 p-4">
          <p className="text-[12.5px] font-medium text-bone-300">Environment Variables</p>
          <p className="mt-1 text-[12.5px] text-bone-500">Add your AccessKeys to the backend <code className="text-bone-300">.env</code> file:</p>
          <code className="mt-3 block whitespace-pre-wrap rounded bg-graphite-800 px-3 py-2 text-[12px] text-bone-100">
            ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key{'\n'}
            ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_secret_key{'\n'}
            ALIBABA_CLOUD_REGION=ap-southeast-1
          </code>
        </div>
      </div>
    </div>
  )
}
