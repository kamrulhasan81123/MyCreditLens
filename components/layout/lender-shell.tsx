'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState } from 'react'
import {
  Bell,
  ClipboardList,
  Cog,
  FileSearch,
  GitCompareArrows,
  LayoutDashboard,
  LogOut,
  Menu,
  PlugZap,
  ScaleIcon,
  ScanLine,
  Search,
  UserRound,
  Users,
  Wallet,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Avatar,
  AvatarFallback,
} from '@/components/ui/avatar'
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
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { cn } from '@/lib/utils'

const NAV = [
  { href: '/lender', label: 'Overview', icon: LayoutDashboard },
  { href: '/lender/applications', label: 'Applications', icon: ClipboardList },
  { href: '/lender/borrowers', label: 'Borrowers', icon: Users },
  { href: '/lender/portfolio', label: 'Portfolio', icon: Wallet },
  { href: '/lender/monitoring', label: 'Model Monitoring', icon: GitCompareArrows },
  { href: '/lender/fairness', label: 'Fairness', icon: ScaleIcon },
  { href: '/lender/audit', label: 'Audit Logs', icon: FileSearch },
  { href: '/lender/api', label: 'API & Integrations', icon: PlugZap },
  { href: '/lender/settings', label: 'Settings', icon: Cog },
]

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname()
  return (
    <nav className="flex flex-1 flex-col gap-1 px-3 py-4" aria-label="Lender navigation">
      {NAV.map((item) => {
        const active =
          item.href === '/lender'
            ? pathname === '/lender'
            : pathname.startsWith(item.href)
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? 'page' : undefined}
            className={cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
              active && 'bg-sidebar-accent text-sidebar-accent-foreground',
            )}
          >
            <item.icon className="size-4.5 shrink-0" aria-hidden />
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}

function SidebarBrand() {
  return (
    <div className="flex h-16 items-center gap-2 border-b border-sidebar-border px-5">
      <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <ScanLine className="size-4.5" aria-hidden />
      </span>
      <div className="flex flex-col leading-tight">
        <span className="text-sm font-semibold text-white">MyCreditLens</span>
        <span className="text-[11px] text-sidebar-foreground">Lender Console</span>
      </div>
    </div>
  )
}

export function LenderShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const router = useRouter()

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-64 shrink-0 flex-col bg-sidebar lg:flex">
        <SidebarBrand />
        <SidebarNav />
        <div className="border-t border-sidebar-border p-3">
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <button className="flex w-full items-center gap-3 rounded-lg p-1.5 text-left transition-colors hover:bg-sidebar-accent">
                  <Avatar className="size-8">
                    <AvatarFallback className="bg-sidebar-accent text-xs text-sidebar-accent-foreground">
                      AR
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col leading-tight">
                    <span className="text-sm font-medium text-white">Aisyah Rahman</span>
                    <span className="text-[11px] text-sidebar-foreground">Credit Analyst</span>
                  </div>
                </button>
              }
            />
            <DropdownMenuContent align="start" side="top" className="w-56">
              <DropdownMenuGroup>
                <DropdownMenuLabel>My account</DropdownMenuLabel>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push('/lender/settings')}>
                <UserRound className="size-4" />
                Profile &amp; settings
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => router.push('/sign-in')}>
                <LogOut className="size-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/90 px-4 backdrop-blur sm:px-6">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger
              render={
                <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open menu">
                  <Menu className="size-5" />
                </Button>
              }
            />
            <SheetContent side="left" className="w-64 bg-sidebar p-0">
              <SheetTitle className="sr-only">Navigation</SheetTitle>
              <SidebarBrand />
              <SidebarNav onNavigate={() => setMobileOpen(false)} />
            </SheetContent>
          </Sheet>

          <div className="relative hidden max-w-sm flex-1 sm:block">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search applications, borrowers, references…"
              className="pl-9"
              aria-label="Search"
            />
          </div>

          <div className="ml-auto flex items-center gap-2">
            <Button size="sm" render={<Link href="/lender/assessments/new" />}>
              New Assessment
            </Button>
            <Button variant="outline" size="icon" aria-label="Notifications">
              <Bell className="size-4.5" />
            </Button>
          </div>
        </header>

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  )
}
