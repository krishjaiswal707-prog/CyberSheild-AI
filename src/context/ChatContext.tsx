import { createContext, useCallback, useMemo, useState, type ReactNode } from 'react'
import type { Message, RiskAnalysis, ScamHistoryEntry } from '@/types'

export interface ChatContextValue {
  messages: Message[]
  isAnalyzing: boolean
  history: ScamHistoryEntry[]
  sendMessage: (content: string) => void
  addBotAnalysis: (analysis: RiskAnalysis, summary?: string) => void
  setTyping: (isTyping: boolean) => void
  clearChat: () => void
}

export const ChatContext = createContext<ChatContextValue | null>(null)

const uid = () => (globalThis.crypto?.randomUUID?.() ?? `m-${Date.now()}-${Math.random().toString(36).slice(2)}`)

const welcome: Message = {
  id: 'welcome',
  type: 'bot',
  content:
    'Hi, I am SafeGuard AI. Paste a message, link, phone number, or upload a screenshot and I will check it for scam signals.',
  timestamp: new Date(),
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([welcome])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [history, setHistory] = useState<ScamHistoryEntry[]>([])

  const setTyping = useCallback((isTyping: boolean) => {
    setIsAnalyzing(isTyping)
  }, [])

  const sendMessage = useCallback((content: string) => {
    if (!content.trim()) return
    setMessages((prev) => [
      ...prev,
      {
        id: uid(),
        type: 'user',
        content: content.trim(),
        timestamp: new Date(),
      },
    ])
    setIsAnalyzing(true)
  }, [])

  const addBotAnalysis = useCallback((analysis: RiskAnalysis, summary?: string) => {
    const id = uid()
    setMessages((prev) => [
      ...prev,
      {
        id,
        type: 'bot',
        content: summary ?? analysis.explanation,
        timestamp: new Date(),
        riskAnalysis: analysis,
      },
    ])
    setHistory((prev) => [
      {
        id,
        date: analysis.analyzedAt ?? new Date(),
        level: analysis.level,
        score: analysis.score,
        sourceType: analysis.sourceType,
        sourceValue: analysis.sourceValue ?? '',
        summary: summary ?? analysis.explanation,
      },
      ...prev,
    ])
    setIsAnalyzing(false)
  }, [])

  const clearChat = useCallback(() => {
    setMessages([welcome])
    setHistory([])
  }, [])

  const value = useMemo(
    () => ({ messages, isAnalyzing, history, sendMessage, addBotAnalysis, setTyping, clearChat }),
    [messages, isAnalyzing, history, sendMessage, addBotAnalysis, setTyping, clearChat],
  )

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}
