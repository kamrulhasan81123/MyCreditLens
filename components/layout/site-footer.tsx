import Link from 'next/link'
import { SiteLogo } from './site-header'

const COLUMNS = [
  {
    title: 'Platform',
    links: [
      { href: '/how-it-works', label: 'How It Works' },
      { href: '/for-lenders', label: 'For Lenders' },
      { href: '/responsible-ai', label: 'Responsible AI' },
    ],
  },
  {
    title: 'Access',
    links: [
      { href: '/sign-in', label: 'Sign In' },
      { href: '/borrower', label: 'Borrower Portal' },
      { href: '/lender', label: 'Lender Dashboard' },
    ],
  },
  {
    title: 'Governance',
    links: [
      { href: '/responsible-ai', label: 'Model Governance' },
      { href: '/responsible-ai', label: 'Fairness Testing' },
      { href: '/responsible-ai', label: 'Data Minimisation' },
    ],
  },
]

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-card">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-[1.5fr_repeat(3,1fr)]">
        <div className="flex flex-col gap-3">
          <SiteLogo />
          <p className="max-w-xs text-sm leading-relaxed text-muted-foreground">
            Explainable alternative-data credit intelligence for borrowers
            traditional models overlook.
          </p>
          <p className="text-xs text-muted-foreground">
            Academic prototype. Not a certified banking system or legally
            approved automated lending platform.
          </p>
        </div>
        {COLUMNS.map((col) => (
          <div key={col.title} className="flex flex-col gap-3">
            <h3 className="text-sm font-semibold text-foreground">{col.title}</h3>
            <ul className="flex flex-col gap-2">
              {col.links.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 py-4 text-xs text-muted-foreground sm:flex-row sm:px-6">
          <span>© {new Date().getFullYear()} MyCreditLens. All rights reserved.</span>
          <span className="inline-flex items-center gap-3">
            <span>Consent-based</span>
            <span aria-hidden>·</span>
            <span>Explainable</span>
            <span aria-hidden>·</span>
            <span>Human-reviewed</span>
          </span>
        </div>
      </div>
    </footer>
  )
}
