'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  FileText,
  Home,
  LogOut,
  MessageSquare,
  Plug,
  ScanLine,
  ShieldCheck,
  UserRound,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Avatar,
  AvatarFallback,
} from '@/components/ui/avatar'
import { cn } from '@/lib/utils'

const NAV = [
  { href: '/borrower', label: 'Dashboard', icon: Home },
  { href: '/borrower/new-application', label: 'New Application', icon: FileText },
  { href: '/borrower/connected-data', label: 'Connected Data', icon: Plug },
  { href: '/borrower/documents', label: 'Documents', icon: FileText },
  { href: '/borrower/consent', label: 'Consent', icon: ShieldCheck },
  { href: '/borrower/messages', label: 'Messages', icon: MessageSquare },
  { href: '/borrower/profile', label: 'Profile', icon: UserRound },
]

const BOTTOM = NAV.filter((n) =>
  ['/borrower', '/borrower/new-application', '/borrower/documents', '/borrower/messages'].includes(
    n.href,
  ),
)

export function BorrowerShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col bg-background">
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/90 px-4 backdrop-blur sm:px-6">
        <Link href="/borrower" className="flex items-center gap-2">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ScanLine className="size-4.5" aria-hidden />
          </span>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold text-navy">MyCreditLens</span>
            <span className="text-[11px] text-muted-foreground">Borrower Portal</span>
          </div>
        </Link>
        <div className="flex items-center gap-1">
          <nav className="hidden items-center gap-1 md:flex" aria-label="Borrower navigation">
            {NAV.slice(0, 6).map((item) => {
              const active =
                item.href === '/borrower'
                  ? pathname === '/borrower'
                  : pathname.startsWith(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'rounded-md px-2.5 py-2 text-sm font-medium text-muted-foreground hover:text-foreground',
                    active && 'text-foreground',
                  )}
                >
                  {item.label}
                </Link>
              )
            })}
          </nav>
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-1 rounded-full"
                  aria-label="Account menu"
                >
                  <Avatar className="size-8">
                    <AvatarFallback className="bg-secondary text-xs text-secondary-foreground">
                      NI
                    </AvatarFallback>
                  </Avatar>
                </Button>
              }
            />
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuGroup>
                <DropdownMenuLabel>Nurul Izzah</DropdownMenuLabel>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push('/borrower/profile')}>
                <UserRound className="size-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => router.push('/borrower/consent')}>
                <ShieldCheck className="size-4" />
                Consent &amp; privacy
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push('/sign-in')}>
                <LogOut className="size-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="flex-1 px-4 py-6 pb-24 sm:px-6 md:pb-6">{children}</main>

      <nav
        className="fixed inset-x-0 bottom-0 z-30 mx-auto flex max-w-5xl items-center justify-around border-t border-border bg-card/95 px-2 py-2 backdrop-blur md:hidden"
        aria-label="Mobile navigation"
      >
        {BOTTOM.map((item) => {
          const active =
            item.href === '/borrower'
              ? pathname === '/borrower'
              : pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center gap-1 rounded-md px-3 py-1.5 text-[11px] font-medium text-muted-foreground',
                active && 'text-primary',
              )}
            >
              <item.icon className="size-5" aria-hidden />
              {item.label.split(' ')[0]}
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
