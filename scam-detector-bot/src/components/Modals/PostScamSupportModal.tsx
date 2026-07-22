import { useCallback } from 'react'
import { LifeBuoy, Phone, FileText, Heart } from 'lucide-react'
import { ModalShell } from '@/components/Modals/ModalShell'
import { useModal } from '@/hooks/useModal'
import { Button } from '@/components/UI/Button'

export function PostScamSupportModal() {
  const { open, closeModal } = useModal()
  const onClose = useCallback(() => closeModal(), [closeModal])

  return (
    <ModalShell
      open={open === 'post-scam'}
      onClose={onClose}
      title="You're not alone"
      description="If you already paid or shared personal info, act quickly — recovery is possible."
    >
      <div className="flex flex-col gap-4">
        <Step
          icon={<Phone size={16} />}
          title="Call 1930 — Cyber Crime Helpline"
          body="Report the fraud immediately. Funds moved within ~2 hours are most recoverable."
        />
        <Step
          icon={<FileText size={16} />}
          title="File a written complaint"
          body="Use cybercrime.gov.in or your nearest cyber cell. Note: keep screenshots ready."
        />
        <Step
          icon={<LifeBuoy size={16} />}
          title="Freeze cards / change passwords"
          body="If card or bank details were shared, freeze the card and rotate passwords + 2FA."
        />
        <Step
          icon={<Heart size={16} />}
          title="Talk to someone"
          body="Scams cause real distress. iCall (9152987821) offers free mental health support."
        />

        <Button variant="secondary" fullWidth onClick={onClose}>
          I have started the steps
        </Button>
      </div>
    </ModalShell>
  )
}

function Step({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode
  title: string
  body: string
}) {
  return (
    <div className="flex items-start gap-3 rounded-card border border-border bg-card p-3">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-pill bg-accent/10 text-accent" aria-hidden="true">
        {icon}
      </span>
      <div>
        <h3 className="text-[14px] font-medium text-text-primary">{title}</h3>
        <p className="mt-0.5 text-[13px] leading-snug text-text-secondary">{body}</p>
      </div>
    </div>
  )
}
