import { forwardRef, type ButtonHTMLAttributes } from 'react'
import type { ButtonSize, ButtonVariant } from '@/types'
import { cn } from '@/lib/risk'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  fullWidth?: boolean
}

const variantClass: Record<ButtonVariant, string> = {
  primary: 'bg-accent text-white hover:brightness-110',
  secondary: 'bg-card text-text-primary border border-border hover:bg-surface',
  ghost: 'bg-transparent text-text-secondary hover:bg-card',
}

const sizeClass: Record<ButtonSize, string> = {
  sm: 'h-9 px-3 text-[13px] rounded-pill',
  md: 'h-11 px-4 text-sm rounded-pill',
  lg: 'h-12 px-5 text-base rounded-pill',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', fullWidth, className, type = 'button', ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium transition-[filter,background-color,transform] duration-200 hover:scale-[1.02] active:scale-100 disabled:opacity-50 disabled:pointer-events-none',
        variantClass[variant],
        sizeClass[size],
        fullWidth && 'w-full',
        className,
      )}
      {...rest}
    />
  )
})
