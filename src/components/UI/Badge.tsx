import type { HTMLAttributes } from 'react'
import type { RiskLevel } from '@/types'
import { cn, riskTextClass, riskBorderClass } from '@/lib/risk'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  level: RiskLevel
  pulse?: boolean
}

export function Badge({ level, pulse, className, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-pill border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wide',
        riskTextClass[level],
        riskBorderClass[level],
        pulse && 'risk-pulse',
        className,
      )}
      {...rest}
    />
  )
}
