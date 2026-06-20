import { useState } from 'react'
import { useMemoryRecords } from '@/hooks/useLiveData'
import { formatRelative, cx } from '@/utils/format'
import { IconMemory, IconCheck } from './icons'
import type { MemoryRecord } from '@/types'

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = score >= 0.9 ? 'bg-signal-remediation' : score >= 0.75 ? 'bg-signal-reporter' : 'bg-signal-detective'
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-graphite-700">
        <div className={cx('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono-data text-[11px] text-bone-500">{pct}%</span>
    </div>
  )
}

function MemoryRow({ record }: { record: MemoryRecord }) {
  return (
    <div className="grid grid-cols-1 gap-3 rounded-lg border border-graphite-700 bg-graphite-900 p-4 md:grid-cols-[1.6fr_1.4fr_0.7fr_0.6fr_0.6fr] md:items-center">
      <div>
        <p className="text-[13.5px] font-medium text-bone-100">{record.incidentTitle}</p>
        <p className="mt-0.5 text-[12px] text-bone-500">{record.rootCause}</p>
      </div>
      <p className="text-[12.5px] text-bone-300">{record.fixApplied}</p>
      <span className="font-mono-data text-[12.5px] text-bone-300">{record.occurrences}x seen</span>
      <ConfidenceBar score={record.confidenceScore} />
      <div>
        {record.autoApplyEligible ? (
          <span className="flex items-center gap-1.5 rounded-md bg-signal-remediation/10 px-2 py-1 font-mono-data text-[10.5px] text-signal-remediation">
            <IconCheck className="h-3 w-3" /> Auto-eligible
          </span>
        ) : (
          <span className="rounded-md bg-graphite-700 px-2 py-1 font-mono-data text-[10.5px] text-bone-500">
            Needs approval
          </span>
        )}
      </div>
    </div>
  )
}

function MemorySkeleton() {
  return (
    <div className="space-y-2.5">
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className="grid grid-cols-1 gap-3 rounded-lg border border-graphite-700 bg-graphite-900 p-4 md:grid-cols-[1.6fr_1.4fr_0.7fr_0.6fr_0.6fr] md:items-center"
        >
          <div className="space-y-2">
            <div className="h-4 w-44 animate-pulse rounded bg-graphite-700" />
            <div className="h-3 w-72 animate-pulse rounded bg-graphite-800" />
          </div>
          <div className="h-3 w-56 animate-pulse rounded bg-graphite-800" />
          <div className="h-3 w-24 animate-pulse rounded bg-graphite-800" />
          <div className="h-3 w-24 animate-pulse rounded bg-graphite-800" />
          <div className="h-6 w-28 animate-pulse rounded bg-graphite-800" />
        </div>
      ))}
    </div>
  )
}

export function MemoryPage() {
  const { memoryRecords, loading } = useMemoryRecords()
  const [query, setQuery] = useState('')
  const normalizedQuery = query.trim().toLowerCase()
  const filteredRecords = normalizedQuery
    ? memoryRecords.filter((record) => {
        const haystack = [
          record.id,
          record.incidentTitle,
          record.rootCause,
          record.fixApplied,
          String(record.occurrences),
        ]
          .join(' ')
          .toLowerCase()
        return haystack.includes(normalizedQuery)
      })
    : memoryRecords

  const hasRecords = filteredRecords.length > 0
  const autoEligible = filteredRecords.filter((record) => record.autoApplyEligible).length
  const avgConfidence = hasRecords
    ? Math.round((filteredRecords.reduce((sum, record) => sum + record.confidenceScore, 0) / filteredRecords.length) * 100)
    : 0
  const mostRecent = hasRecords
    ? filteredRecords.reduce((latest, record) => (new Date(record.lastSeen) > new Date(latest.lastSeen) ? record : latest))
    : null

  return (
    <div className="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-[20px] font-semibold text-bone-100">Memory Vault</h1>
          <p className="mt-1 text-[13px] text-bone-500">
            Every resolved incident is stored here. When the same pattern recurs, Aegis can skip straight to the fix.
          </p>
        </div>
        <div className="flex w-full flex-col gap-2 sm:w-auto sm:min-w-[320px]">
          <label className="font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500">Search memory</label>
          <div className="flex gap-2">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search incidents, fixes, root causes, or try Fork bomb"
              className="min-w-0 flex-1 rounded-md border border-graphite-700 bg-graphite-900 px-3 py-2 text-[13px] text-bone-100 placeholder:text-bone-500/60 focus:border-signal-detective"
            />
            <button
              onClick={() => setQuery('Fork bomb')}
              className="rounded-md border border-signal-diagnostician/30 bg-signal-diagnostician/10 px-3 py-2 text-[13px] font-semibold text-signal-diagnostician"
            >
              Try Fork bomb
            </button>
          </div>
          {query && (
            <button
              onClick={() => setQuery('')}
              className="self-start font-mono-data text-[11px] text-bone-500 hover:text-bone-300"
            >
              Clear search
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          { label: 'Patterns learned', value: filteredRecords.length },
          { label: 'Total occurrences', value: filteredRecords.reduce((sum, record) => sum + record.occurrences, 0) },
          { label: 'Auto-eligible', value: autoEligible },
          { label: 'Avg. confidence', value: `${avgConfidence}%` },
        ].map((stat) => (
          <div key={stat.label} className="rounded-lg border border-graphite-700 bg-graphite-900 p-4">
            <p className="font-mono-data text-[20px] font-semibold text-bone-100">{stat.value}</p>
            <p className="mt-0.5 text-[12px] text-bone-500">{stat.label}</p>
          </div>
        ))}
      </div>

      {loading ? (
        <MemorySkeleton />
      ) : !hasRecords ? (
        <p className="rounded-lg border border-dashed border-graphite-600 px-4 py-8 text-center text-[13px] text-bone-500">
          {query
            ? `No memory entries matched "${query}". Try searching for Fork bomb.`
            : "No incidents have been resolved yet - Aegis hasn't learned any patterns."}
        </p>
      ) : (
        <>
          <div className="hidden grid-cols-[1.6fr_1.4fr_0.7fr_0.6fr_0.6fr] gap-3 px-4 font-mono-data text-[10.5px] uppercase tracking-wide text-bone-500 md:grid">
            <span>Incident pattern</span>
            <span>Fix applied</span>
            <span>Frequency</span>
            <span>Confidence</span>
            <span>Status</span>
          </div>

          <div className="space-y-2.5">
            {filteredRecords.map((record) => (
              <MemoryRow key={record.id} record={record} />
            ))}
          </div>

          {mostRecent && (
            <div className="flex items-center gap-2.5 rounded-lg border border-dashed border-graphite-600 px-4 py-3.5 text-[12.5px] text-bone-500">
              <IconMemory className="h-4 w-4 text-signal-diagnostician" />
              Last memory write: {formatRelative(mostRecent.lastSeen)} - vector similarity threshold set to 0.85
            </div>
          )}
        </>
      )}
    </div>
  )
}
