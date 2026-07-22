import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/risk'
import type { ConfidenceFactor } from '@/types'

export interface ConfidenceBreakdownProps {
  confidence: number
  factors?: ConfidenceFactor[]
}

export function ConfidenceBreakdown({ confidence, factors }: ConfidenceBreakdownProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-card border border-border bg-surface">
      <button
        type="button"
        aria-expanded={open}
        aria-controls="confidence-breakdown-body"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-3 py-2.5 text-left"
      >
        <span className="flex items-center gap-2 text-[13px] font-medium text-text-primary">
          Model confidence
          <span className="tabular-nums text-text-secondary">{confidence}%</span>
        </span>
        <span
          className={cn(
            'transition-transform duration-300 text-text-secondary',
            open && 'rotate-180',
          )}
          aria-hidden="true"
        >
          <ChevronDown size={16} />
        </span>
      </button>

      <AnimatePresence initial={false}>
        {open && factors && factors.length > 0 && (
          <motion.div
            id="confidence-breakdown-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <ul className="flex flex-col gap-2 px-3 pb-3" aria-label="Confidence factors">
              {factors.map((f) => (
                <li key={f.id} className="flex flex-col gap-1">
                  <div className="flex items-center justify-between text-[12px]">
                    <span className="text-text-secondary">{f.label}</span>
                    <span className="tabular-nums text-text-muted">
                      {Math.round(f.value * 100)}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-pill bg-card">
                    <motion.div
                      className="h-full rounded-pill bg-accent"
                      initial={{ width: 0 }}
                      animate={{ width: `${f.value * 100}%` }}
                      transition={{ duration: 0.6, ease: 'easeOut' }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
