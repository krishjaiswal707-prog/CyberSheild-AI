import { AlertTriangle } from 'lucide-react'
import type { RedFlag, RiskLevel } from '@/types'
import { cn, riskTextClass } from '@/lib/risk'

export interface RedFlagsListProps {
  flags: RedFlag[]
  maxVisible?: number
}

export function RedFlagsList({ flags, maxVisible = 6 }: RedFlagsListProps) {
  const visible = flags.slice(0, maxVisible)

  if (visible.length === 0) {
    return (
      <p className="text-[13px] text-text-secondary">
        No specific red flags matched. Continue with normal caution.
      </p>
    )
  }

  return (
    <ul className="flex flex-col gap-2" aria-label="Detected red flags">
      {visible.map((flag) => (
        <li
          key={flag.id}
          className="flex items-start gap-2.5 rounded-card bg-surface px-3 py-2"
        >
          <AlertTriangle
            className={cn('mt-0.5 shrink-0', riskTextClass[flag.severity])}
            size={16}
            aria-hidden="true"
          />
          <span className="text-[13px] leading-snug text-text-primary">{flag.text}</span>
        </li>
      ))}
    </ul>
  )
}

export function severityRank(level: RiskLevel): number {
  return { SAFE: 0, LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4 }[level]
}
