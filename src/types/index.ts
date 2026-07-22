export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'SAFE'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost'

export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ActionButton {
  id: string
  label: string
  icon?: string
  onClick: () => void
  variant: ButtonVariant
}

export interface RedFlag {
  id: string
  text: string
  severity: RiskLevel
}

export interface ConfidenceFactor {
  id: string
  label: string
  weight: number
  value: number
}

export interface RiskAnalysis {
  score: number
  level: RiskLevel
  confidence: number
  redFlags: RedFlag[]
  explanation: string
  actions: ActionButton[]
  confidenceFactors?: ConfidenceFactor[]
  sourceType?: 'url' | 'phone' | 'text' | 'image' | 'qr'
  sourceValue?: string
  analyzedAt?: Date
}

export interface Message {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
  riskAnalysis?: RiskAnalysis
  isTyping?: boolean
}

export type SidebarTab = 'dashboard' | 'history' | 'links'

export interface QuickLink {
  id: string
  label: string
  url: string
  description: string
  category: 'hotline' | 'portal' | 'resource'
}

export interface ScamHistoryEntry {
  id: string
  date: Date
  level: RiskLevel
  score: number
  sourceType: RiskAnalysis['sourceType']
  sourceValue: string
  summary: string
}

export interface UserPrefs {
  notifications: boolean
  autoAnalyze: boolean
  language: 'en' | 'hi' | 'ta' | 'te' | 'bn'
  soundOnMessage: boolean
}

export type ModalKind = 'settings' | 'post-scam' | 'detail' | null
