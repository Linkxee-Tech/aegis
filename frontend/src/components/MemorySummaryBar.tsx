import type { MemoryRecord } from '@/types'
import { IconMemory } from './icons'

interface MemorySummaryBarProps {
  records: MemoryRecord[]
}

export function MemorySummaryBar({ records }: MemorySummaryBarProps) {
  const totalIncidents = records.reduce((sum, r) => sum + r.occurrences, 0)
  const autoEligible = records.filter((r) => r.autoApplyEligible).length
  const resolutionRate = Math.round((autoEligible / records.length) * 100)

  return (
    <div className="flex flex-wrap items-center gap-4 rounded-lg border border-graphite-700 bg-graphite-900 px-5 py-3.5">
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-signal-diagnostician/10">
          <IconMemory className="h-4 w-4 text-signal-diagnostician" />
        </div>
        <span className="text-[13.5px] font-medium text-bone-100">Memory Agent</span>
      </div>
      <span className="font-mono-data text-[12.5px] text-bone-500">
        <span className="text-bone-100">{totalIncidents}</span> incidents remembered
      </span>
      <span className="hidden h-3 w-px bg-graphite-600 sm:block" />
      <span className="font-mono-data text-[12.5px] text-bone-500">
        <span className="text-signal-remediation">{resolutionRate}%</span> auto-resolution rate
      </span>
      <span className="hidden h-3 w-px bg-graphite-600 sm:block" />
      <span className="font-mono-data text-[12.5px] text-bone-500">
        <span className="text-bone-100">{records.length}</span> known patterns
      </span>
    </div>
  )
}
