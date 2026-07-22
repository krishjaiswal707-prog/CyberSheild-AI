import { motion } from 'framer-motion'
import { memo } from 'react'
import { formatTime } from '@/lib/risk'
import type { Message } from '@/types'

export interface UserMessageProps {
  message: Message
}

function UserMessageBase({ message }: UserMessageProps) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="flex justify-end"
      role="article"
      aria-label="Your message"
    >
      <div className="flex max-w-[85%] flex-col items-end gap-0.5">
        <div className="rounded-bubble rounded-br-2 bg-user-bubble px-3.5 py-2 text-[14px] text-white">
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>
        <time
          className="px-1 text-[10px] text-text-muted"
          dateTime={message.timestamp.toISOString()}
        >
          {formatTime(message.timestamp)}
        </time>
      </div>
    </motion.div>
  )
}

export const UserMessage = memo(UserMessageBase)
