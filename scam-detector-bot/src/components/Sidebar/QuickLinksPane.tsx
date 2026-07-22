import { ExternalLink, Phone, FileText } from 'lucide-react'
import type { QuickLink } from '@/types'

const LINKS: QuickLink[] = [
  {
    id: '1930',
    label: 'Cyber Crime Helpline — 1930',
    url: 'https://cybercrime.gov.in',
    description: 'Report financial fraud / cyber crime (Indian Cyber Crime Coordination Centre).',
    category: 'hotline',
  },
  {
    id: 'ncrb',
    label: 'NCRB Online Complaint',
    url: 'https://ncrb.gov.in/complaints',
    description: 'File a formal complaint with the National Crime Records Bureau.',
    category: 'portal',
  },
  {
    id: 'rbi-ombudsman',
    label: 'RBI Banking Ombudsman',
    url: 'https://rbi.org.in/Scripts/FeedbackNotification.aspx',
    description: 'Grievance against banks / unauthorised transactions.',
    category: 'portal',
  },
]

function iconForCategory(category: QuickLink['category']) {
  if (category === 'hotline') return Phone
  if (category === 'portal') return FileText
  return ExternalLink
}

export function QuickLinksPane({ collapsed }: { collapsed: boolean }) {
  if (collapsed) {
    return (
      <div className="flex justify-center py-2 text-text-muted" aria-label="Quick links, sidebar collapsed">
        <ExternalLink size={18} />
      </div>
    )
  }

  return (
    <ul className="flex flex-col gap-2" aria-label="Helpful quick links and hotlines">
      {LINKS.map((link) => {
        const Icon = iconForCategory(link.category)
        return (
          <li key={link.id}>
            <a
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-start gap-3 rounded-card border border-border bg-card p-3 transition-colors hover:border-accent"
              aria-label={`${link.label} (opens external link)`}
            >
              <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-pill bg-surface text-accent" aria-hidden="true">
                <Icon size={16} />
              </span>
              <span className="flex flex-col">
                <span className="flex items-center gap-1 text-[13px] font-medium text-text-primary">
                  {link.label}
                  <ExternalLink
                    size={12}
                    className="text-text-muted opacity-0 transition-opacity group-hover:opacity-100"
                    aria-hidden="true"
                  />
                </span>
                <span className="mt-0.5 text-[12px] leading-snug text-text-secondary">
                  {link.description}
                </span>
              </span>
            </a>
          </li>
        )
      })}
    </ul>
  )
}
