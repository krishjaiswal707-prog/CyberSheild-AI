import { useCallback } from 'react'
import { ModalShell } from '@/components/Modals/ModalShell'
import { useModal } from '@/hooks/useModal'
import { RiskBadge } from '@/components/Cards/RiskBadge'
import { RiskScoreCircle } from '@/components/Cards/RiskScoreCircle'
import { RedFlagsList } from '@/components/Cards/RedFlagsList'

export function DetailModal() {
  const { open, closeModal, detailPayload } = useModal()
  const onClose = useCallback(() => closeModal(), [closeModal])

  const analysis = detailPayload

  return (
    <ModalShell
      open={open === 'detail'}
      onClose={onClose}
      title="Full risk analysis"
      description={analysis ? analysis.explanation : 'No analysis selected.'}
    >
      {!analysis ? (
        <p className="text-[13px] text-text-secondary">
          Select a scan from the chat to see the full breakdown here.
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-4">
            <RiskScoreCircle score={analysis.score} level={analysis.level} size={96} />
            <div className="flex flex-col gap-2">
              <RiskBadge level={analysis.level} pulse={analysis.level === 'CRITICAL'} />
              <p className="text-[13px] text-text-secondary">
                Confidence: <span className="tabular-nums">{analysis.confidence}%</span>
              </p>
              {analysis.sourceValue && (
                <p className="break-words text-[12px] text-text-muted">
                  Source: <code className="rounded bg-card px-1 py-0.5">{analysis.sourceValue}</code>
                </p>
              )}
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wide text-text-muted">
              Red flags ({analysis.redFlags.length})
            </h3>
            <RedFlagsList flags={analysis.redFlags} maxVisible={20} />
          </div>

          <details className="rounded-card border border-border bg-card p-3 text-[13px]">
            <summary className="cursor-pointer font-medium text-text-primary">
              Explanation
            </summary>
            <p className="mt-2 text-text-secondary">{analysis.explanation}</p>
          </details>
        </div>
      )}
    </ModalShell>
  )
}
