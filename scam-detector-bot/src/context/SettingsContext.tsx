import { createContext, useCallback, useMemo, useState, type ReactNode } from 'react'
import type { UserPrefs } from '@/types'

export interface SettingsContextValue {
  prefs: UserPrefs
  setPrefs: (p: UserPrefs) => void
  updatePref: <K extends keyof UserPrefs>(key: K, value: UserPrefs[K]) => void
  sidebarCollapsed: boolean
  setSidebarCollapsed: (collapsed: boolean) => void
  toggleSidebar: () => void
  mobileNavOpen: boolean
  setMobileNavOpen: (open: boolean) => void
  toggleMobileNav: () => void
}



export const SettingsContext = createContext<SettingsContextValue | null>(null)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefsState] = useState<UserPrefs>({
    notifications: true,
    autoAnalyze: true,
    language: 'en',
    soundOnMessage: false,
  })
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const setPrefs = useCallback((p: UserPrefs) => {
    setPrefsState(p)
  }, [])

  const updatePref = useCallback(
    <K extends keyof UserPrefs>(key: K, value: UserPrefs[K]) => {
      setPrefsState((prev) => ({ ...prev, [key]: value }))
    },
    [],
  )

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => !prev)
  }, [])

  const toggleMobileNav = useCallback(() => {
    setMobileNavOpen((prev) => !prev)
  }, [])

  const value = useMemo(
    () => ({
      prefs,
      setPrefs,
      updatePref,
      sidebarCollapsed,
      setSidebarCollapsed,
      toggleSidebar,
      mobileNavOpen,
      setMobileNavOpen,
      toggleMobileNav,
    }),
    [prefs, updatePref, sidebarCollapsed, toggleSidebar, mobileNavOpen, toggleMobileNav],
  )

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}
