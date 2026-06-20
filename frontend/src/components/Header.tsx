import { useState } from 'react'
import { cx } from '@/utils/format'

interface HeaderProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

const TABS = ['Dashboard', 'Incidents', 'Reports', 'Memory', 'Settings']

function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" xmlns="http://www.w3.org/2000/svg">
      {open ? (
        <path d="M6 6L18 18M18 6L6 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      ) : (
        <path d="M4 7H20M4 12H20M4 17H20" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      )}
    </svg>
  )
}

export function Header({ activeTab, onTabChange }: HeaderProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  function selectTab(tab: string) {
    onTabChange(tab)
    setMobileOpen(false)
  }

  return (
    <header className="sticky top-0 z-40 border-b border-graphite-700 bg-graphite-950/90 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-md border border-graphite-600 bg-graphite-900">
              <img
                src="/aegis-mark.svg"
                alt="Aegis"
                className="h-full w-full object-cover object-top"
              />
            </div>
            <span className="font-display text-[17px] font-bold tracking-tight text-bone-100">
              AEGIS
            </span>
          </div>
          <nav className="hidden items-center gap-1 md:flex">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => selectTab(tab)}
                className={cx(
                  'rounded-md px-3.5 py-2 text-[13.5px] font-medium transition-colors',
                  activeTab === tab
                    ? 'bg-graphite-700 text-bone-100'
                    : 'text-bone-500 hover:text-bone-300'
                )}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-md border border-graphite-600 px-2.5 py-1.5 sm:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-signal-remediation" />
            <span className="font-mono-data text-[11px] text-bone-500">ap-southeast-1</span>
          </div>
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-graphite-700 font-mono-data text-[12px] font-semibold text-bone-300">
            A
          </div>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle navigation menu"
            aria-expanded={mobileOpen}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-graphite-600 text-bone-300 md:hidden"
          >
            <MenuIcon open={mobileOpen} />
          </button>
        </div>
      </div>

      {mobileOpen && (
        <nav className="border-t border-graphite-700 bg-graphite-950 px-4 py-2 md:hidden">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => selectTab(tab)}
              className={cx(
                'block w-full rounded-md px-3 py-2.5 text-left text-[14px] font-medium transition-colors',
                activeTab === tab ? 'bg-graphite-700 text-bone-100' : 'text-bone-500'
              )}
            >
              {tab}
            </button>
          ))}
        </nav>
      )}
    </header>
  )
}
