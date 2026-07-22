import { memo, useCallback } from 'react'
import { PanelLeft, Settings, Shield, Menu } from 'lucide-react'
import { useSettings } from '@/hooks/useSettings'
import { useModal } from '@/hooks/useModal'

function HeaderBase() {
  const { toggleSidebar, toggleMobileNav } = useSettings()
  const { openModal } = useModal()

  const onSettings = useCallback(() => openModal('settings'), [openModal])

  return (
    <header
      className="sticky top-0 z-20 flex h-14 shrink-0 items-center justify-between border-b border-border bg-bg/95 px-3 sm:px-4"
      role="banner"
    >
      <div className="flex items-center gap-2">
        <button
          type="button"
          aria-label="Toggle sidebar"
          onClick={toggleSidebar}
          className="hidden h-9 w-9 items-center justify-center rounded-pill text-text-secondary transition-colors hover:bg-card hover:text-text-primary sm:flex"
          title="Toggle sidebar"
        >
          <PanelLeft size={18} aria-hidden="true" />
        </button>
        <button
          type="button"
          aria-label="Open menu"
          onClick={toggleMobileNav}
          className="flex h-9 w-9 items-center justify-center rounded-pill text-text-secondary transition-colors hover:bg-card hover:text-text-primary sm:hidden"
        >
          <Menu size={18} aria-hidden="true" />
        </button>

        <div className="flex items-center gap-2" aria-label="CyberSheild-AI">
          <span className="flex h-8 w-8 items-center justify-center rounded-pill bg-risk-safe/10">
            <Shield size={16} className="text-risk-safe" aria-hidden="true" />
          </span>
          <div className="flex flex-col leading-none">
            <h1 className="text-[15px] font-semibold text-text-primary">CyberSheild-AI</h1>
            <p className="text-[11px] text-text-muted">Digital Arrest Scam Detector</p>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={onSettings}
        aria-label="Open settings"
        className="flex h-9 w-9 items-center justify-center rounded-pill text-text-secondary transition-colors hover:bg-card hover:text-text-primary"
      >
        <Settings size={18} aria-hidden="true" />
      </button>
    </header>
  )
}

export const Header = memo(HeaderBase)
