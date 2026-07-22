import { History, Inbox } from 'lucide-react'
import { useChat } from '@/hooks/useChat'
import { Badge } from '@/components/UI/Badge'
import { formatDate, cn } from '@/lib/risk'

export function ScamHistoryPane({ collapsed }: { collapsed: boolean }) {
  const { history } = useChat()

  if (collapsed) {
    return (
      <div className="flex justify-center py-2 text-text-muted" aria-label="No history, sidebar collapsed">
        <History size={18} />
      </div>
    )
  }

  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-8 text-text-muted" role="status">
        <Inbox size={28} aria-hidden="true" />
        <p className="text-[13px]">No scam history yet.</p>
      </div>
    )
  }

  return (
    <ol className="relative flex flex-col gap-3" aria-label="Scan history timeline">
      <span
        className="absolute left-2.5 top-1 h-full w-px bg-border"
        aria-hidden="true"
      />
      {history.map((entry) => (
        <li key={entry.id} className="relative pl-7">
          <span
            className={cn(
              'absolute left-1.5 top-1.5 h-2.5 w-2.5 rounded-full border-2 border-bg',
              entry.level === 'CRITICAL' && 'bg-risk-critical',
              entry.level === 'HIGH' && 'bg-risk-high',
              entry.level === 'MEDIUM' && 'bg-risk-medium',
              entry.level === 'LOW' && 'bg-risk-low',
              entry.level === 'SAFE' && 'bg-risk-safe',
            )}
            aria-hidden="true"
          />
          <div className="flex items-start justify-between gap-2">
            <p className="line-clamp-2 text-[13px] text-text-primary">{entry.summary}</p>
            <span className="shrink-0 tabular-nums text-[12px] text-text-muted">
              {entry.score}
            </span>
          </div>
          <div className="mt-1 flex items-center justify-between">
            <time className="text-[11px] text-text-muted" dateTime={entry.date.toISOString()}>
              {formatDate(entry.date)}
            </time>
            <Badge level={entry.level} />
          </div>
        </li>
      ))}
    </ol>
  )
}
