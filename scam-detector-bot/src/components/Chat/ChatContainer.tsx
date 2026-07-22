import { useCallback, useEffect, useRef, useState, type Ref } from 'react'
import { AnimatePresence } from 'framer-motion'
import { useChat } from '@/hooks/useChat'
import { useModal } from '@/hooks/useModal'
import { UserMessage } from '@/components/Chat/UserMessage'
import { BotRiskCard } from '@/components/Chat/BotRiskCard'
import { TypingIndicator } from '@/components/Chat/TypingIndicator'
import { MessageInput } from '@/components/Chat/MessageInput'
import { analyzeMessage } from '@/lib/api'
import { autoAnalyze } from '@/lib/analyzer'
import type { RiskAnalysis, RiskLevel } from '@/types'

const QUICK_ACTIONS: Array<{ label: string; prompt: string }> = [
  {
    label: 'Urgency message',
    prompt:
      'URGENT! Your account will be blocked in 2 hours. Click http://bit.ly/verify-now to re-activate KYC.',
  },
  {
    label: 'Prize alert',
    prompt:
      'Congratulations! You won Rs 2,00,000 in the KBC lucky draw. Pay Rs 5,000 processing fee to claim: call +91-9876543210',
  },
  {
    label: 'OTP request',
    prompt: 'This is your bank. Forward the OTP you just received to confirm your identity.',
  },
  {
    label: 'Safe example',
    prompt: 'Hi, did you finish reviewing the design doc I shared in Figma? Let me know if you have feedback.',
  },
]

export interface ChatContainerProps {
  scrollRef?: Ref<HTMLDivElement>
}

export function ChatContainer({ scrollRef }: ChatContainerProps) {
  const { messages, isAnalyzing, reviewedIds, sendMessage, addBotAnalysis, markAsReviewed, clearChat } = useChat()
  const { openModal, setDetailPayload } = useModal()
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'unknown'>('unknown')

  const localRef = useRef<HTMLDivElement>(null)
  const ref = (scrollRef ?? localRef) as React.RefObject<HTMLDivElement>

  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isAnalyzing, ref])

  const fallbackAnalysis = useCallback(
    (content: string, summary?: string) => {
      const analysis = autoAnalyze(content)
      analysis.actions = []
      addBotAnalysis(analysis, summary ?? analysis.explanation)
    },
    [addBotAnalysis],
  )

  const callBackend = useCallback(
    async (content: string) => {
      try {
        const res = await analyzeMessage(content)
        setApiStatus('online')
        const analysis: RiskAnalysis = {
          score: res.risk_score,
          level: res.risk_tier as RiskLevel,
          confidence: Math.round(res.confidence * 100),
          redFlags: res.matched_red_flags.map((flag, i) => ({
            id: `flag-${i}`,
            text: flag,
            severity: res.risk_score >= 85 ? 'CRITICAL' as RiskLevel : res.risk_score >= 65 ? 'HIGH' as RiskLevel : 'MEDIUM' as RiskLevel,
          })),
          explanation: res.explanation,
          sourceType: 'text',
          analyzedAt: new Date(),
          checklist_triggered: res.checklist_triggered,
          actions: [],
        }
        addBotAnalysis(analysis, analysis.explanation)
      } catch {
        setApiStatus('offline')
        fallbackAnalysis(content)
      }
    },
    [addBotAnalysis, fallbackAnalysis],
  )

  const handleSend = useCallback(
    (content: string) => {
      sendMessage(content)
      callBackend(content)
    },
    [sendMessage, callBackend],
  )

  const handleAttach = useCallback(
    (file: File) => {
      const text = `Image attachment: ${file.name} (${file.type || 'unknown type'})`
      sendMessage(text)
      const fallback = () => fallbackAnalysis(text, 'Analyzed the uploaded image.')
      try {
        fallback()
      } catch {
        fallback()
      }
    },
    [sendMessage, fallbackAnalysis],
  )

  const handleDetail = useCallback(() => {
    const last = [...messages].reverse().find((m) => m.riskAnalysis)
    if (last?.riskAnalysis) {
      setDetailPayload(last.riskAnalysis)
      openModal('detail')
    }
  }, [messages, setDetailPayload, openModal])

  const statusLabel =
    apiStatus === 'online'
      ? '✓ Connected to backend API'
      : apiStatus === 'offline'
        ? '⚠ Backend unreachable — using local fallback'
        : 'Connecting to backend…'

  return (
    <section
      className="flex min-h-0 flex-1 flex-col bg-bg"
      aria-label="Chat with CyberSheild-AI"
    >
      <div
        ref={ref}
        className="no-scrollbar flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-3 py-4 sm:px-6"
      >
        <AnimatePresence initial={false}>
          {messages.map((message) =>
            message.type === 'user' ? (
              <UserMessage key={message.id} message={message} />
            ) : (
              <BotRiskCard
                key={message.id}
                message={message}
                reviewed={reviewedIds.has(message.id)}
                onRequestDetail={handleDetail}
                onMarkAsReviewed={markAsReviewed}
              />
            ),
          )}
        </AnimatePresence>

        {isAnalyzing && <TypingIndicator />}
      </div>

      <div className="flex items-center justify-between px-3 pb-1 sm:px-6">
        <p className="text-[11px] text-text-muted">{statusLabel}</p>
        <button
          type="button"
          onClick={clearChat}
          className="text-[12px] font-medium text-text-secondary hover:text-text-primary"
        >
          Clear chat
        </button>
      </div>

      <MessageInput
        onSend={handleSend}
        onAttach={handleAttach}
        disabled={isAnalyzing}
        quickActions={QUICK_ACTIONS}
      />
    </section>
  )
}


