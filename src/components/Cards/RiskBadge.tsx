import { Badge } from '@/components/UI/Badge'
import type { RiskLevel } from '@/types'

export interface RiskBadgeProps {
  level: RiskLevel
  pulse?: boolean
  className?: string
}

const labelCopy: Record<RiskLevel, string> = {
  CRITICAL: 'Critical Risk',
  HIGH: 'High Risk',
  MEDIUM: 'Medium Risk',
  LOW: 'Low Risk',
  SAFE: 'Safe',
}

export function RiskBadge({ level, pulse, className }: RiskBadgeProps) {
  return (
    <Badge level={level} pulse={pulse} className={className} aria-label={`Risk level: ${labelCopy[level]}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
      {labelCopy[level]}
    </Badge>
  )
}
