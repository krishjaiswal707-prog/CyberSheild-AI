import { memo } from 'react'
import { Shield } from 'lucide-react'

function TypingIndicatorBase() {
  return (
    <div
      className="flex items-center gap-2"
      role="status"
      aria-label="SafeGuard AI is analyzing your message"
    >
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-pill bg-risk-safe/10">
        <Shield size={14} className="text-risk-safe" aria-hidden="true" />
      </div>
      <div className="flex items-center gap-1 rounded-bubble rounded-bl-2 bg-card px-3.5 py-2.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="typing-dot h-1.5 w-1.5 rounded-full bg-text-muted"
            style={{ animationDelay: `${i * 0.15}s` }}
            aria-hidden="true"
          />
        ))}
      </div>
    </div>
  )
}

export const TypingIndicator = memo(TypingIndicatorBase)
