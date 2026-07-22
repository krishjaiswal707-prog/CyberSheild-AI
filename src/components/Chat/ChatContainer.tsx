import { useCallback, useEffect, useRef, type Ref } from 'react'
import { AnimatePresence } from 'framer-motion'
import { useChat } from '@/hooks/useChat'
import { useModal } from '@/hooks/useModal'
import { UserMessage } from '@/components/Chat/UserMessage'
import { BotRiskCard } from '@/components/Chat/BotRiskCard'
import { TypingIndicator } from '@/components/Chat/TypingIndicator'
import { MessageInput } from '@/components/Chat/MessageInput'
import { autoAnalyze } from '@/lib/analyzer'

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
  const { messages, isAnalyzing, sendMessage, addBotAnalysis, clearChat } = useChat()
  const { openModal, setDetailPayload } = useModal()

  const localRef = useRef<HTMLDivElement>(null)
  const ref = (scrollRef ?? localRef) as React.RefObject<HTMLDivElement>

  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isAnalyzing, ref])

  const handleSend = useCallback(
    (content: string) => {
      sendMessage(content)
      const analysis = autoAnalyze(content)
      window.setTimeout(() => addBotAnalysis(analysis, analysis.explanation), 1100)
    },
    [sendMessage, addBotAnalysis],
  )

  const handleAttach = useCallback(
    (file: File) => {
      const text = `Image attachment: ${file.name} (${file.type || 'unknown type'})`
      sendMessage(text)
      const analysis = autoAnalyze(text)
      analysis.sourceType = 'image'
      analysis.sourceValue = file.name
      window.setTimeout(
        () => addBotAnalysis(analysis, 'Analyzed the uploaded image.'),
        1400,
      )
    },
    [sendMessage, addBotAnalysis],
  )

  const handleDetail = useCallback(() => {
    const last = [...messages].reverse().find((m) => m.riskAnalysis)
    if (last?.riskAnalysis) {
      setDetailPayload(last.riskAnalysis)
      openModal('detail')
    }
  }, [messages, setDetailPayload, openModal])

  return (
    <section
      className="flex min-h-0 flex-1 flex-col bg-bg"
      aria-label="Chat with SafeGuard AI"
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
                onRequestDetail={handleDetail}
              />
            ),
          )}
        </AnimatePresence>

        {isAnalyzing && <TypingIndicator />}
      </div>

      <div className="flex items-center justify-between px-3 pb-1 sm:px-6">
        <p className="text-[11px] text-text-muted">Demo analyzer runs locally in your browser.</p>
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
