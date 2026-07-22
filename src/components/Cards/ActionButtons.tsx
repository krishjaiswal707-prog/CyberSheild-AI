import { motion } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'
import {
  Ban,
  Flag,
  FileText,
  LifeBuoy,
  Bell,
  BookOpen,
  Check,
  type LucideProps,
} from 'lucide-react'
import { Button } from '@/components/UI/Button'
import type { ActionButton as ActionButtonData } from '@/types'

export interface ActionButtonsProps {
  actions: ActionButtonData[]
}

const iconMap: Record<string, LucideIcon> = {
  block: Ban,
  report: Flag,
  complaint: FileText,
  recovery: LifeBuoy,
  notify: Bell,
  learn: BookOpen,
  reviewed: Check,
}

function iconFor(label: string): LucideIcon {
  const key = label.toLowerCase()
  if (key.includes('block')) return iconMap.block
  if (key.includes('report')) return iconMap.report
  if (key.includes('complaint') || key.includes('ncrb')) return iconMap.complaint
  if (key.includes('recovery') || key.includes('help')) return iconMap.recovery
  if (key.includes('notify') || key.includes('alert')) return iconMap.notify
  if (key.includes('learn')) return iconMap.learn
  return iconMap.reviewed
}

export function ActionButtons({ actions }: ActionButtonsProps) {
  if (actions.length === 0) return null

  return (
    <div className="flex flex-col gap-2">
      {actions.map((action, idx) => {
        const Icon = iconFor(action.label)
        const IconComp = (props: LucideProps) => <Icon size={16} {...props} />
        return (
          <motion.div
            key={action.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: idx * 0.04 }}
          >
            <Button
              variant={action.variant}
              fullWidth
              onClick={action.onClick}
              aria-label={action.label}
            >
              <IconComp aria-hidden="true" />
              {action.label}
            </Button>
          </motion.div>
        )
      })}
    </div>
  )
}
