import type { ActionButton, RiskAnalysis, RiskLevel } from '@/types'
import { levelFromScore } from './risk'

const SCAM_SIGNALS: Array<{ re: RegExp; score: number; flag: string; severity: RiskLevel }> = [
  { re: /urgent|immediately|right now|act now/i, score: 12, flag: 'Uses urgency language to pressure quick action', severity: 'HIGH' },
  { re: /bitcoin|crypto|investment|double your|guaranteed return/i, score: 18, flag: 'Promises of guaranteed/unsolicited investment returns', severity: 'CRITICAL' },
  { re: /reward|prize|lottery|won|winner|kyc|verification fee/i, score: 16, flag: 'Advance-fee / prize bait (pay to release winnings)', severity: 'CRITICAL' },
  { re: /otp|one[- ]?time password|share.*code|forward.*code/i, score: 20, flag: 'Asks you to share or forward an OTP', severity: 'CRITICAL' },
  { re: /http:\/\/|bit\.ly|tinyurl|t\.me|wa\.me/i, score: 8, flag: 'Contains shortened or unencrypted http link', severity: 'MEDIUM' },
  { re: /\b\d{6,}\b.+?(account|verify|block)/i, score: 10, flag: 'Suspicious reference number tied to account action', severity: 'HIGH' },
  { re: /click here|tap now|verify now|confirm now/i, score: 6, flag: 'Generic "click/verify now" call to action', severity: 'MEDIUM' },
  { re: /kyc|update.*details|suspended.*account|reactivate/i, score: 14, flag: 'Fake KYC / account suspension scare', severity: 'HIGH' },
  { re: /prize|gift|free|bonus|cashback/i, score: 6, flag: 'Unsolicited free gift / cashback offer', severity: 'MEDIUM' },
  { re: /bh?ank|rbi|income tax|customs|parcel/i, score: 12, flag: 'Impersonates an authority (bank / RBI / customs)', severity: 'HIGH' },
]

export interface AnalyzeInput {
  content: string
  sourceType?: RiskAnalysis['sourceType']
  sourceValue?: string
}

export function analyzeContent({ content, sourceType, sourceValue }: AnalyzeInput): RiskAnalysis {
  const text = sourceValue ? `${content} ${sourceValue}` : content
  let score = 5
  const redFlags: RiskAnalysis['redFlags'] = []

  for (const signal of SCAM_SIGNALS) {
    if (signal.re.test(text)) {
      score += signal.score
      redFlags.push({ id: crypto.randomUUID(), text: signal.flag, severity: signal.severity })
    }
  }

  if (sourceType === 'phone') score += 10
  if (sourceType === 'url') score += 6
  if (sourceType === 'qr') score += 15

  const clamped = Math.min(100, Math.max(0, score))
  const level = levelFromScore(clamped)
  const confidence = Math.min(98, 60 + redFlags.length * 6)

  const explanation = explain(level, redFlags.length)

  const actions: ActionButton[] = buildActions(level)

  return {
    score: clamped,
    level,
    confidence,
    redFlags: redFlags.slice(0, 6),
    explanation,
    actions,
    sourceType,
    sourceValue,
    analyzedAt: new Date(),
    confidenceFactors: [
      { id: 'f1', label: 'Language patterns', weight: 0.4, value: Math.min(1, redFlags.length / 4) },
      { id: 'f2', label: 'Source reputation', weight: 0.3, value: sourceType === 'url' ? 0.7 : 0.3 },
      { id: 'f3', label: 'Signal density', weight: 0.3, value: Math.min(1, redFlags.length / 5) },
    ],
  }
}

function explain(level: RiskLevel, flagCount: number): string {
  const base: Record<RiskLevel, string> = {
    SAFE: 'No scam signals detected in this content. Stay cautious, but this looks legitimate.',
    LOW: 'Minor red flags detected. Verify the sender independently before taking action.',
    MEDIUM: 'Several scam signals detected. Do not click links, share OTPs, or send money.',
    HIGH: 'Strong scam signals detected. Block the sender and report this conversation.',
    CRITICAL: 'Critical scam pattern detected. Do not pay, share codes, or click anything. Report now.',
  }
  const flags = flagCount > 0 ? ` ${flagCount} red flag${flagCount === 1 ? '' : 's'} identified.` : ''
  return base[level] + flags
}

function buildActions(level: RiskLevel): ActionButton[] {
  const noop = () => {}
  if (level === 'SAFE' || level === 'LOW') {
    return [
      { id: 'a1', label: 'Mark as reviewed', onClick: noop, variant: 'primary' },
      { id: 'a2', label: 'Learn scam signs', onClick: noop, variant: 'secondary' },
    ]
  }
  return [
    { id: 'a1', label: 'Block sender', onClick: noop, variant: 'primary' },
    { id: 'a2', label: 'Report on WhatsApp', onClick: noop, variant: 'primary' },
    { id: 'a3', label: 'File NCRB complaint', onClick: noop, variant: 'secondary' },
    { id: 'a4', label: 'Get recovery help', onClick: noop, variant: 'secondary' },
  ]
}

function detectSource(input: string): { sourceType: RiskAnalysis['sourceType']; sourceValue?: string } {
  const trimmed = input.trim()
  const url = trimmed.match(/https?:\/\/[^\s]+|t\.me\/[^\s]+|wa\.me\/[^\s]+|bit\.ly\/[^\s]+/i)
  if (url) return { sourceType: 'url', sourceValue: url[0] }
  const phone = trimmed.match(/\+?\d[\d\s-]{8,}/)
  if (phone) return { sourceType: 'phone', sourceValue: phone[0] }
  return { sourceType: 'text' }
}

export function autoAnalyze(content: string): RiskAnalysis {
  const { sourceType, sourceValue } = detectSource(content)
  return analyzeContent({ content, sourceType, sourceValue })
}
