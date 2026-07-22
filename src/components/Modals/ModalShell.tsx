import { useEffect, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import { cn } from '@/lib/risk'

export interface ModalShellProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  variant?: 'drawer' | 'modal'
  children: ReactNode
  labelledById?: string
  widthClass?: string
}

export function ModalShell({
  open,
  onClose,
  title,
  description,
  variant = 'modal',
  children,
  labelledById = 'modal-title',
  widthClass,
}: ModalShellProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <AnimatePresence>
      {open && (
        <div
          className="fixed inset-0 z-50 flex"
          role="dialog"
          aria-modal="true"
          aria-labelledby={labelledById}
          aria-describedby={description ? 'modal-desc' : undefined}
        >
          <motion.button
            type="button"
            aria-label="Close dialog"
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="absolute inset-0 bg-bg/70"
          />

          {variant === 'drawer' ? (
            <motion.section
              key="drawer"
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              className={cn(
                'ml-auto flex h-full w-[320px] max-w-[90vw] flex-col border-l border-border bg-surface',
                widthClass,
              )}
            >
              <ModalHeader title={title} description={description} onClose={onClose} />
              <div className="no-scrollbar flex-1 overflow-y-auto p-4">{children}</div>
            </motion.section>
          ) : (
            <motion.section
              key="modal"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className={cn(
                'relative m-auto w-[min(560px,92vw)] rounded-modal border border-border bg-surface',
                widthClass,
              )}
            >
              <ModalHeader title={title} description={description} onClose={onClose} />
              <div className="no-scrollbar max-h-[70vh] overflow-y-auto p-4">{children}</div>
            </motion.section>
          )}
        </div>
      )}
    </AnimatePresence>
  )
}

function ModalHeader({
  title,
  description,
  onClose,
}: {
  title: string
  description?: string
  onClose: () => void
}) {
  return (
    <header className="flex items-start justify-between gap-3 border-b border-border px-4 py-3">
      <div>
        <h2 id="modal-title" className="text-base font-semibold text-text-primary">
          {title}
        </h2>
        {description && (
          <p id="modal-desc" className="mt-0.5 text-[13px] text-text-secondary">
            {description}
          </p>
        )}
      </div>
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-pill text-text-secondary transition-colors hover:bg-card hover:text-text-primary"
      >
        <X size={18} aria-hidden="true" />
      </button>
    </header>
  )
}
