import { IconCheck } from './icons'

export function UserGuidePage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-6 sm:px-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div>
        <h1 className="font-display text-[20px] font-semibold text-bone-100">User Guide</h1>
        <p className="mt-1 text-[13px] text-bone-500">
          Welcome to Aegis! Here is how to use the application and understand the multi-agent workflow.
        </p>
      </div>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
        <h2 className="flex items-center gap-2 font-display text-[15px] font-medium text-bone-100">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-graphite-800 text-[12px] text-bone-300">1</span>
          Simulate an Incident
        </h2>
        <p className="mt-2 text-[13px] text-bone-400">
          On the Dashboard, click the <strong>Simulate Incident</strong> button to trigger a mock anomaly (e.g., a memory usage spike). This will kickstart the entire autonomous agent pipeline, allowing you to watch the system in action.
        </p>
      </div>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
        <h2 className="flex items-center gap-2 font-display text-[15px] font-medium text-bone-100">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-graphite-800 text-[12px] text-bone-300">2</span>
          Observe the Agents
        </h2>
        <p className="mt-2 text-[13px] text-bone-400">
          Once an incident is triggered, the agents will begin working sequentially:
        </p>
        <ul className="mt-3 space-y-2 pl-4 text-[13px] text-bone-400 list-disc">
          <li><strong>Detective Agent:</strong> Constantly monitors metrics and logs to detect the anomaly.</li>
          <li><strong>Diagnostician Agent:</strong> Analyzes the evidence to find the root cause of the issue.</li>
          <li><strong>Remediation Agent:</strong> Proposes a step-by-step fix for the root cause and waits for your approval.</li>
          <li><strong>Reporter Agent:</strong> Documents the entire incident and files a final report.</li>
        </ul>
      </div>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
        <h2 className="flex items-center gap-2 font-display text-[15px] font-medium text-bone-100">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-graphite-800 text-[12px] text-bone-300">3</span>
          Human Approval Checkpoint
        </h2>
        <p className="mt-2 text-[13px] text-bone-400">
          Aegis will never touch your live servers without permission. When the Remediation Agent proposes a fix, the incident will enter an <strong>Awaiting Approval</strong> state. You must review the proposed bash/Python commands and explicitly click <strong>Confirm</strong> to execute them on your live servers.
        </p>
      </div>

      <div className="rounded-lg border border-graphite-700 bg-graphite-900 p-5">
        <h2 className="flex items-center gap-2 font-display text-[15px] font-medium text-bone-100">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-graphite-800 text-[12px] text-bone-300">4</span>
          Memory System
        </h2>
        <p className="mt-2 text-[13px] text-bone-400">
          After an incident is resolved, it is stored in the Memory Knowledge Base. If the same incident happens again in the future, the system will recognize the pattern and can auto-resolve it instantly if it meets your confidence threshold. You can manage this in the <strong>Memory</strong> tab.
        </p>
      </div>
    </div>
  )
}
