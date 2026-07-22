import { createContext, useCallback, useMemo, useState, type ReactNode } from 'react'
import type { ModalKind, RiskAnalysis } from '@/types'

export interface ModalContextValue {
  open: ModalKind
  openModal: (kind: ModalKind) => void
  closeModal: () => void
  detailPayload: RiskAnalysis | null
  setDetailPayload: (analysis: RiskAnalysis | null) => void
}

export const ModalContext = createContext<ModalContextValue | null>(null)

export function ModalProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState<ModalKind>(null)
  const [detailPayload, setDetailPayload] = useState<RiskAnalysis | null>(null)

  const openModal = useCallback((kind: ModalKind) => setOpen(kind), [])
  const closeModal = useCallback(() => setOpen(null), [])

  const value = useMemo(
    () => ({ open, openModal, closeModal, detailPayload, setDetailPayload }),
    [open, openModal, closeModal, detailPayload],
  )

  return <ModalContext.Provider value={value}>{children}</ModalContext.Provider>
}
