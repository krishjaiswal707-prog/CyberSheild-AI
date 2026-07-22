import { useEffect, useState } from 'react'

export function useDebouncedValue<T>(value: T, delay = 200): T {
  const [debounced, setDebounced] = useState<T>(value)

  useEffect(() => {
    const timer = globalThis.setTimeout(() => setDebounced(value), delay)
    return () => globalThis.clearTimeout(timer)
  }, [value, delay])

  return debounced
}
