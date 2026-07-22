import { TrendingUp, ShieldCheck, AlertOctagon } from 'lucide-react'
import { Badge } from '@/components/UI/Badge'
import { useChat } from '@/hooks/useChat'
import { cn } from '@/lib/risk'
import type { RiskLevel } from '@/types'

export function DashboardPane({ collapsed }: { collapsed: boolean }) {
  const { history } = useChat()

  if (collapsed) {
    return (
      <div className="flex justify-center py-2 text-text-muted" aria-label="No data, sidebar collapsed">
        <TrendingUp size={18} />
      </div>
    )
  }

  const total = history.length
  const counts: Record<RiskLevel, number> = {
    CRITICAL: 0,
    HIGH: 0,
    MEDIUM: 0,
    LOW: 0,
    SAFE: 0,
  }
  for (const entry of history) counts[entry.level] += 1
  const lastScore = history[0]?.score ?? null
  const lastLevel = history[0]?.level ?? null

  return (
    <div className="flex flex-col gap-4" aria-label="Your risk profile">
      <section className="rounded-card border border-border bg-card p-3">
        <h3 className="text-[11px] font-medium uppercase tracking-wide text-text-muted">
          Risk profile
        </h3>
        <div className="mt-2 flex items-center justify-between">
          <span className="text-2xl font-semibold tabular-nums">{total}</span>
          <span className="text-[12px] text-text-secondary">analyses</span>
        </div>
      </section>

      <section className="rounded-card border border-border bg-card p-3">
        <h3 className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-text-muted">
          <TrendingUp size={12} /> Last scan
        </h3>
        {lastLevel ? (
          <p className="mt-2 flex items-center justify-between">
            <Badge level={lastLevel} />
            <span className="tabular-nums text-[13px] text-text-secondary">
              {lastScore as number}/100
            </span>
          </p>
        ) : (
          <p className="mt-2 text-[13px] text-text-secondary">No scans yet.</p>
        )}
      </section>

      <section className="rounded-card border border-border bg-card p-3" aria-label="Breakdown by risk level">
        <h3 className="text-[11px] font-medium uppercase tracking-wide text-text-muted">
          By risk level
        </h3>
        <ul className="mt-2 flex flex-col gap-1.5">
          {(Object.keys(counts) as RiskLevel[]).map((level) => (
            <li key={level} className="flex items-center justify-between text-[13px]">
              <span className="flex items-center gap-2">
                <span
                  className={cn(
                    'h-2 w-2 rounded-full',
                    level === 'CRITICAL' && 'bg-risk-critical',
                    level === 'HIGH' && 'bg-risk-high',
                    level === 'MEDIUM' && 'bg-risk-medium',
                    level === 'LOW' && 'bg-risk-low',
                    level === 'SAFE' && 'bg-risk-safe',
                  )}
                  aria-hidden="true"
                />
                <span className="text-text-secondary">{level.toLowerCase()}</span>
              </span>
              <span className="tabular-nums text-text-primary">{counts[level]}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-card border border-border bg-card p-3">
        <h3 className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-text-muted">
          {total > 0 ? <AlertOctagon size={12} /> : <ShieldCheck size={12} />}
          Tip
        </h3>
        <p className="mt-1.5 text-[13px] leading-snug text-text-secondary">
          {total === 0
            ? 'Run your first scan by pasting a message on the right.'
            : 'Block and report senders that share OTP or payment requests.'}
        </p>
      </section>
    </div>
  )
}
