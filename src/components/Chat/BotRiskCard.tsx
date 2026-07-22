import { memo, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Shield } from 'lucide-react'
import { formatTime } from '@/lib/risk'
import type { Message } from '@/types'
import { RiskBadge } from '@/components/Cards/RiskBadge'
import { RiskScoreCircle } from '@/components/Cards/RiskScoreCircle'
import { RedFlagsList } from '@/components/Cards/RedFlagsList'
import { ConfidenceBreakdown } from '@/components/Cards/ConfidenceBreakdown'
import { ActionButtons } from '@/components/Cards/ActionButtons'

export interface BotRiskCardProps {
  message: Message
  onRequestDetail?: (messageId: string) => void
}

function BotRiskCardBase({ message, onRequestDetail }: BotRiskCardProps) {
  const analysis = message.riskAnalysis

  const handleDetail = useCallback(() => {
    onRequestDetail?.(message.id)
  }, [onRequestDetail, message.id])

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="flex w-full max-w-[85%] flex-col gap-2"
      role="article"
      aria-label="CyberSheild-AI risk analysis"
    >
      <div className="flex items-center gap-2">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-pill bg-risk-safe/10">
          <Shield size={14} className="text-risk-safe" aria-hidden="true" />
        </div>
        <span className="text-[13px] font-medium text-text-primary">CyberSheild-AI</span>
        <time
          className="text-[10px] text-text-muted"
          dateTime={message.timestamp.toISOString()}
        >
          {formatTime(message.timestamp)}
        </time>
      </div>

      {!analysis ? (
        <div className="rounded-bubble rounded-bl-2 bg-card px-3.5 py-2.5 text-[14px] text-text-primary">
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>
      ) : (
        <div
          className="rounded-modal border border-border bg-card p-3.5 sm:p-4"
          aria-label={`Risk level: ${analysis.level}, score ${analysis.score}`}
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
            <div className="flex shrink-0 justify-center">
              <RiskScoreCircle score={analysis.score} level={analysis.level} size={112} />
            </div>

            <div className="flex min-w-0 flex-1 flex-col gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <RiskBadge level={analysis.level} pulse={analysis.level === 'CRITICAL'} />
                {analysis.sourceType && (
                  <span className="rounded-pill border border-border bg-surface px-2 py-0.5 text-[11px] uppercase tracking-wide text-text-muted">
                    {analysis.sourceType}
                  </span>
                )}
              </div>

              <p className="text-[13px] leading-snug text-text-secondary">
                {analysis.explanation}
              </p>

              {analysis.redFlags.length > 0 && (
                <div>
                  <h4 className="mb-2 text-[11px] font-medium uppercase tracking-wide text-text-muted">
                    Red flags ({analysis.redFlags.length})
                  </h4>
                  <RedFlagsList flags={analysis.redFlags} />
                </div>
              )}

              <ConfidenceBreakdown
                confidence={analysis.confidence}
                factors={analysis.confidenceFactors}
              />

              <ActionButtons actions={analysis.actions} />

              <button
                type="button"
                onClick={handleDetail}
                className="self-start text-[12px] font-medium text-accent transition-colors hover:text-white"
              >
                View full analysis →
              </button>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  )
}

export const BotRiskCard = memo(BotRiskCardBase)
