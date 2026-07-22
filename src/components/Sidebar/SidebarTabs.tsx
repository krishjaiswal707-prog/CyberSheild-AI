import { useCallback, useState } from 'react'
import { LayoutDashboard, History, Link2 } from 'lucide-react'
import { TabNavigation } from '@/components/UI/TabNavigation'
import { DashboardPane } from '@/components/Sidebar/DashboardPane'
import { ScamHistoryPane } from '@/components/Sidebar/ScamHistoryPane'
import { QuickLinksPane } from '@/components/Sidebar/QuickLinksPane'
import { useSettings } from '@/hooks/useSettings'
import type { SidebarTab } from '@/types'

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={16} /> },
  { id: 'history', label: 'History', icon: <History size={16} /> },
  { id: 'links', label: 'Quick Links', icon: <Link2 size={16} /> },
] as const

export function SidebarTabs() {
  const [active, setActive] = useState<SidebarTab>('dashboard')
  const { sidebarCollapsed } = useSettings()

  const onChange = useCallback((id: SidebarTab) => setActive(id), [])

  return (
    <div className="flex h-full flex-col gap-3 overflow-hidden">
      <TabNavigation
        tabs={[...TABS]}
        active={active}
        onChange={onChange}
        layout="vertical"
        collapsed={sidebarCollapsed}
      />

      <div className="no-scrollbar min-h-0 flex-1 overflow-y-auto">
        {active === 'dashboard' && <DashboardPane collapsed={sidebarCollapsed} />}
        {active === 'history' && <ScamHistoryPane collapsed={sidebarCollapsed} />}
        {active === 'links' && <QuickLinksPane collapsed={sidebarCollapsed} />}
      </div>
    </div>
  )
}
