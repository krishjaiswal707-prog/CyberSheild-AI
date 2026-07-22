import { useCallback } from 'react'
import { ModalShell } from '@/components/Modals/ModalShell'
import { useSettings } from '@/hooks/useSettings'
import { useModal } from '@/hooks/useModal'
import type { UserPrefs } from '@/types'

const LANGS: Array<{ value: UserPrefs['language']; label: string }> = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'हिन्दी' },
  { value: 'ta', label: 'தமிழ்' },
  { value: 'te', label: 'తెలుగు' },
  { value: 'bn', label: 'বাংলা' },
]

export function SettingsDrawer() {
  const { open, closeModal } = useModal()
  const { prefs, updatePref } = useSettings()

  const onClose = useCallback(() => closeModal(), [closeModal])

  return (
    <ModalShell
      open={open === 'settings'}
      onClose={onClose}
      variant="drawer"
      title="Settings"
      description="Customize how SafeGuard AI behaves."
    >
      <div className="flex flex-col gap-5">
        <ToggleRow
          label="Notifications"
          description="Get notified about high-risk scans."
          checked={prefs.notifications}
          onChange={(v) => updatePref('notifications', v)}
        />
        <ToggleRow
          label="Auto-analyze pasted text"
          description="Run the analyzer as soon as you send a message."
          checked={prefs.autoAnalyze}
          onChange={(v) => updatePref('autoAnalyze', v)}
        />
        <ToggleRow
          label="Message sounds"
          description="Play a subtle sound when a scan completes."
          checked={prefs.soundOnMessage}
          onChange={(v) => updatePref('soundOnMessage', v)}
        />

        <div>
          <label
            htmlFor="settings-language"
            className="block text-[13px] font-medium text-text-primary"
          >
            Language
          </label>
          <p className="mb-2 mt-0.5 text-[12px] text-text-secondary">
            UI and analysis summaries.
          </p>
          <select
            id="settings-language"
            value={prefs.language}
            onChange={(e) =>
              updatePref('language', e.target.value as UserPrefs['language'])
            }
            className="h-10 w-full rounded-pill border border-border bg-card px-3 text-[14px] text-text-primary focus:border-accent"
          >
            {LANGS.map((l) => (
              <option key={l.value} value={l.value}>
                {l.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </ModalShell>
  )
}

interface ToggleRowProps {
  label: string
  description: string
  checked: boolean
  onChange: (v: boolean) => void
}

function ToggleRow({ label, description, checked, onChange }: ToggleRowProps) {
  return (
    <label className="flex items-start justify-between gap-4">
      <span className="flex flex-col">
        <span className="text-[14px] font-medium text-text-primary">{label}</span>
        <span className="mt-0.5 text-[12px] text-text-secondary">{description}</span>
      </span>
      <span className="relative mt-0.5 inline-flex h-6 w-11 shrink-0">
        <input
          type="checkbox"
          className="peer sr-only"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          aria-label={label}
        />
        <span className="absolute inset-0 rounded-pill bg-border transition-colors peer-checked:bg-accent" />
        <span className="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform peer-checked:translate-x-5" />
      </span>
    </label>
  )
}
