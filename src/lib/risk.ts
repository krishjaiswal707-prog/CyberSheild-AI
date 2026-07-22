import type { RiskLevel } from '@/types'

export const riskLevelOrder: Record<RiskLevel, number> = {
  SAFE: 0,
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  CRITICAL: 4,
}

export const riskColorToken: Record<RiskLevel, string> = {
  CRITICAL: 'var(--color-risk-critical)',
  HIGH: 'var(--color-risk-high)',
  MEDIUM: 'var(--color-risk-medium)',
  LOW: 'var(--color-risk-low)',
  SAFE: 'var(--color-risk-safe)',
}

export const riskTextClass: Record<RiskLevel, string> = {
  CRITICAL: 'text-risk-critical',
  HIGH: 'text-risk-high',
  MEDIUM: 'text-risk-medium',
  LOW: 'text-risk-low',
  SAFE: 'text-risk-safe',
}

export const riskBgClass: Record<RiskLevel, string> = {
  CRITICAL: 'bg-risk-critical',
  HIGH: 'bg-risk-high',
  MEDIUM: 'bg-risk-medium',
  LOW: 'bg-risk-low',
  SAFE: 'bg-risk-safe',
}

export const riskBorderClass: Record<RiskLevel, string> = {
  CRITICAL: 'border-risk-critical',
  HIGH: 'border-risk-high',
  MEDIUM: 'border-risk-medium',
  LOW: 'border-risk-low',
  SAFE: 'border-risk-safe',
}

export function levelFromScore(score: number): RiskLevel {
  if (score >= 85) return 'CRITICAL'
  if (score >= 65) return 'HIGH'
  if (score >= 40) return 'MEDIUM'
  if (score >= 20) return 'LOW'
  return 'SAFE'
}

export function labelForScore(score: number): string {
  return levelFromScore(score).toLowerCase()
}

export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}

export function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(date)
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(date)
}

export const easeOutBack = [0.34, 1.56, 0.64, 1] as const
export const easeOutCubic = [0.22, 1, 0.36, 1] as const
