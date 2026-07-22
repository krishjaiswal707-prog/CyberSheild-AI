import { useEffect, useRef, useState } from 'react'
import { motion, useInView } from 'framer-motion'
import { cn, riskColorToken } from '@/lib/risk'
import type { RiskLevel } from '@/types'

export interface RiskScoreCircleProps {
  score: number
  level: RiskLevel
  size?: number
  strokeWidth?: number
  className?: string
}

export function RiskScoreCircle({
  score,
  level,
  size = 120,
  strokeWidth = 10,
  className,
}: RiskScoreCircleProps) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, amount: 0.5 })

  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const clamped = Math.min(100, Math.max(0, score))
  const targetOffset = circumference - (clamped / 100) * circumference
  const [offset, setOffset] = useState(circumference)

  useEffect(() => {
    if (!inView) return
    const id = globalThis.requestAnimationFrame(() => setOffset(targetOffset))
    return () => globalThis.cancelAnimationFrame(id)
  }, [inView, targetOffset])

  const color = riskColorToken[level]
  const center = size / 2

  return (
    <div
      ref={ref}
      className={cn('relative inline-flex items-center justify-center', className)}
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Risk score ${Math.round(clamped)} out of 100, level ${level.toLowerCase()}`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={strokeWidth}
        />
        <motion.circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          transform={`rotate(-90 ${center} ${center})`}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transition={{ duration: 1.2, ease: [0.34, 1.56, 0.64, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-semibold tabular-nums" style={{ color }}>
          {Math.round(clamped)}
        </span>
        <span className="mt-0.5 text-[10px] uppercase tracking-wide text-text-muted">risk score</span>
      </div>
    </div>
  )
}
