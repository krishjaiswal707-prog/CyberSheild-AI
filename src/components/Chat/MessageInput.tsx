import { useCallback, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { Send, Paperclip } from 'lucide-react'
import { Chip } from '@/components/UI/Chip'
import { cn } from '@/lib/risk'

export interface MessageInputProps {
  onSend: (content: string) => void
  onAttach?: (file: File) => void
  disabled?: boolean
  quickActions?: Array<{ label: string; prompt: string }>
}

const MAX_LEN = 2000

export function MessageInput({
  onSend,
  onAttach,
  disabled,
  quickActions = [],
}: MessageInputProps) {
  const [value, setValue] = useState('')
  const [fileError, setFileError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const submit = useCallback(
    (event?: FormEvent) => {
      event?.preventDefault()
      const trimmed = value.trim()
      if (!trimmed || disabled) return
      onSend(trimmed)
      setValue('')
    },
    [value, disabled, onSend],
  )

  const handleChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.value.length <= MAX_LEN) setValue(e.target.value)
  }, [])

  const handleFile = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return
      if (file.size > 5_000_000) {
        setFileError('File too large (max 5MB)')
        e.target.value = ''
        return
      }
      setFileError(null)
      onAttach?.(file)
      e.target.value = ''
    },
    [onAttach],
  )

  const triggerFile = useCallback(() => {
    fileRef.current?.click()
  }, [])

  return (
    <form
      onSubmit={submit}
      className="flex flex-col gap-2 border-t border-border bg-bg/95 px-2 py-2 sm:px-4 sm:py-3"
      aria-label="Send a message to SafeGuard AI"
    >
      {quickActions.length > 0 && (
        <div className="no-scrollbar flex gap-2 overflow-x-auto" role="group">
          {quickActions.map((qa) => (
            <Chip
              key={qa.label}
              label={qa.label}
              onClick={() => onSend(qa.prompt)}
              disabled={disabled}
            />
          ))}
        </div>
      )}

      <div className="flex items-end gap-2">
        <button
          type="button"
          onClick={triggerFile}
          aria-label="Attach screenshot or QR code"
          disabled={disabled}
          className={cn(
            'flex h-11 w-11 shrink-0 items-center justify-center rounded-pill border border-border bg-card text-text-secondary transition-colors hover:text-text-primary',
            disabled && 'opacity-50 pointer-events-none',
          )}
        >
          <Paperclip size={18} aria-hidden="true" />
        </button>

        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="sr-only"
          onChange={handleFile}
          aria-label="Upload screenshot"
        />

        <label htmlFor="safeguard-input" className="sr-only">
          Type a message, link, or phone number to scan
        </label>
        <input
          id="safeguard-input"
          type="text"
          value={value}
          onChange={handleChange}
          placeholder="Paste message, link, or phone number…"
          maxLength={MAX_LEN}
          disabled={disabled}
          autoComplete="off"
          className={cn(
            'h-11 min-w-0 flex-1 rounded-pill border border-border bg-card px-4 text-[14px] text-text-primary placeholder:text-text-muted',
            'transition-colors focus:border-accent',
          )}
        />

        <button
          type="submit"
          aria-label="Send message"
          disabled={disabled || !value.trim()}
          className={cn(
            'flex h-11 w-11 shrink-0 items-center justify-center rounded-pill bg-accent text-white transition-[filter,transform]',
            'hover:brightness-110 hover:scale-[1.02] active:scale-100',
            'disabled:opacity-40 disabled:pointer-events-none',
          )}
        >
          <Send size={18} aria-hidden="true" />
        </button>
      </div>

      {fileError && (
        <p role="alert" className="px-1 text-[12px] text-risk-high">
          {fileError}
        </p>
      )}
    </form>
  )
}
