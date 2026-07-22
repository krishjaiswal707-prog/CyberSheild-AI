import { memo, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useSettings } from '@/hooks/useSettings'
import { SidebarTabs } from '@/components/Sidebar/SidebarTabs'
import { cn } from '@/lib/risk'

function SidebarBase() {
  const { sidebarCollapsed } = useSettings()

  return (
    <>
      <motion.aside
        aria-label="Navigation"
        className={cn(
          'hidden shrink-0 flex-col border-r border-border bg-surface md:flex',
          sidebarCollapsed ? 'w-16' : 'w-[280px]',
        )}
        animate={{ width: sidebarCollapsed ? 64 : 280 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="h-full overflow-hidden px-2 py-3">
          <SidebarTabs />
        </div>
      </motion.aside>

      <MobileSidebar />
    </>
  )
}

function MobileSidebar() {
  const { mobileNavOpen, setMobileNavOpen } = useSettings()

  useEffect(() => {
    if (!mobileNavOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileNavOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [mobileNavOpen, setMobileNavOpen])

  return (
    <div className="md:hidden" aria-hidden={!mobileNavOpen}>
      <AnimatePresence>
        {mobileNavOpen && (
          <motion.button
            key="overlay"
            type="button"
            aria-label="Close navigation"
            onClick={() => setMobileNavOpen(false)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 top-14 z-30 bg-bg/70"
          />
        )}
      </AnimatePresence>

      <motion.aside
        aria-label="Mobile navigation"
        initial={false}
        animate={{ x: mobileNavOpen ? 0 : -280 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="fixed left-0 top-14 z-40 h-[calc(100%-3.5rem)] w-[280px] border-r border-border bg-surface"
      >
        <div className="h-full overflow-hidden px-2 py-3">
          <SidebarTabs />
        </div>
      </motion.aside>
    </div>
  )
}

export const Sidebar = memo(SidebarBase)
