import type { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/risk'

export interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string
  active?: boolean
}

export function Chip({ label, active, className, type = 'button', ...rest }: ChipProps) {
  return (
    <button
      type={type}
      className={cn(
        'inline-flex shrink-0 items-center gap-1.5 rounded-pill border px-3 py-1.5 text-[13px] transition-colors duration-200 hover:scale-[1.02]',
        active
          ? 'bg-accent text-white border-accent'
          : 'bg-card text-text-secondary border-border hover:text-text-primary',
        className,
      )}
      {...rest}
    >
      {label}
    </button>
  )
}
