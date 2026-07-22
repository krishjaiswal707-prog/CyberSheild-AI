import { motion } from 'framer-motion'
import { cn } from '@/lib/risk'
import type { SidebarTab } from '@/types'

export interface TabNavigationProps {
  tabs: Array<{ id: SidebarTab; label: string; icon: React.ReactNode }>
  active: SidebarTab
  onChange: (id: SidebarTab) => void
  layout?: 'horizontal' | 'vertical'
  collapsed?: boolean
}

export function TabNavigation({
  tabs,
  active,
  onChange,
  layout = 'horizontal',
  collapsed,
}: TabNavigationProps) {
  return (
    <nav
      aria-label="Sections"
      className={cn(
        layout === 'vertical' ? 'flex flex-col gap-1' : 'flex flex-row gap-1',
      )}
    >
      {tabs.map((tab) => {
        const isActive = tab.id === active
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            aria-label={tab.label}
            onClick={() => onChange(tab.id)}
            className={cn(
              'relative flex items-center gap-2.5 rounded-pill px-3 py-2 text-[13px] font-medium transition-colors',
              layout === 'vertical' ? 'w-full' : '',
              collapsed ? 'justify-center' : 'justify-start',
              isActive ? 'text-text-primary' : 'text-text-secondary hover:text-text-primary',
            )}
          >
            {isActive && (
              <motion.span
                layoutId={`tab-bg-${layout}`}
                transition={{ duration: 0.25, ease: 'easeOut' }}
                className={cn(
                  'absolute inset-0 rounded-pill bg-card',
                  layout === 'vertical' && 'border-l-2 border-accent rounded-none rounded-pill',
                )}
              />
            )}
            <span className="relative z-10" aria-hidden={collapsed ? undefined : true}>
              {tab.icon}
            </span>
            {!collapsed && <span className="relative z-10">{tab.label}</span>}
          </button>
        )
      })}
    </nav>
  )
}
