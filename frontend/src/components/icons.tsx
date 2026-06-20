interface IconProps {
  className?: string
}

export function IconDetective({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10.5" cy="10.5" r="6" stroke="currentColor" strokeWidth="1.6" />
      <path d="M15 15L20 20" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M7.5 10.5L9.5 8L11 11.5L13.5 7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function IconDiagnostician({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 3V11C6 14 8 16 12 16C16 16 18 14 18 11V3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="6" cy="3" r="1.4" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="18" cy="3" r="1.4" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="12" cy="20" r="2.4" stroke="currentColor" strokeWidth="1.6" />
      <path d="M12 16V17.6" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  )
}

export function IconRemediation({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M14.7 6.3L17.7 9.3M8.5 12.5L4 17L7 20L11.5 15.5M12.8 11.2L16.2 7.8C17 7 18.3 7 19.1 7.8C19.9 8.6 19.9 9.9 19.1 10.7L15.7 14.1L12.8 11.2Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function IconReporter({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="5" y="3" width="14" height="18" rx="1.4" stroke="currentColor" strokeWidth="1.6" />
      <path d="M8 8H16M8 12H16M8 16H12.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

export function IconMemory({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M12 4C7.6 4 4 7.1 4 11C4 13.4 5.4 15.5 7.5 16.7V19.5L10 18.3C10.6 18.4 11.3 18.5 12 18.5C16.4 18.5 20 15.4 20 11.5C20 7.6 16.4 4 12 4Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <circle cx="9" cy="11" r="0.9" fill="currentColor" />
      <circle cx="12" cy="11" r="0.9" fill="currentColor" />
      <circle cx="15" cy="11" r="0.9" fill="currentColor" />
    </svg>
  )
}

export function IconShield({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 3L20 6.5V12C20 17 16.5 20.5 12 22C7.5 20.5 4 17 4 12V6.5L12 3Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M8.5 12.5H10.5L11.7 8.5L14 16L15.2 12.5H16.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function IconCheck({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M5 13L9.5 17.5L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function IconX({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 6L18 18M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export function IconChevronDown({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 9L12 15L18 9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function IconAlertTriangle({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 4L21 19H3L12 4Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M12 10V14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="12" cy="16.6" r="0.9" fill="currentColor" />
    </svg>
  )
}

export function IconLock({ className, locked = true }: IconProps & { locked?: boolean }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="5" y="11" width="14" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      {locked ? (
        <path d="M8 11V8C8 5.8 9.8 4 12 4C14.2 4 16 5.8 16 8V11" stroke="currentColor" strokeWidth="1.6" />
      ) : (
        <path d="M8 11V8C8 5.8 9.8 4 12 4C13.7 4 15.2 5 15.7 6.4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      )}
      <circle cx="12" cy="15" r="1.3" fill="currentColor" />
    </svg>
  )
}

export function IconDownload({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 4V15M12 15L8 11M12 15L16 11" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5 17V18.5C5 19.3 5.7 20 6.5 20H17.5C18.3 20 19 19.3 19 18.5V17" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  )
}

export function IconClock({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="8.5" stroke="currentColor" strokeWidth="1.6" />
      <path d="M12 7.5V12L15 14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function IconServer({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="4" y="4" width="16" height="6" rx="1.2" stroke="currentColor" strokeWidth="1.6" />
      <rect x="4" y="14" width="16" height="6" rx="1.2" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="7.5" cy="7" r="0.8" fill="currentColor" />
      <circle cx="7.5" cy="17" r="0.8" fill="currentColor" />
    </svg>
  )
}
