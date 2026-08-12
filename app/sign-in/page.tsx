'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import {
  Building2,
  Eye,
  EyeOff,
  Lock,
  ScanLine,
  ShieldCheck,
  TriangleAlert,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { useAuth } from '@/lib/auth-context'

type Role = 'lender' | 'borrower'

const ROLE_DEFAULT_EMAIL: Record<Role, string> = {
  lender: 'analyst@lender.example',
  borrower: 'nurul@borrower.example',
}

export default function SignInPage() {
  const router = useRouter()
  const { login, isLoading: authLoading } = useAuth()
  const [role, setRole] = useState<Role>('lender')
  const [email, setEmail] = useState(ROLE_DEFAULT_EMAIL.lender)
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [mfaRequired, setMfaRequired] = useState(false)
  const [mfaCode, setMfaCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function switchRole(next: Role) {
    if (next === role) return
    setRole(next)
    setEmail(ROLE_DEFAULT_EMAIL[next])
    setPassword('')
    setMfaRequired(false)
    setMfaCode('')
    setError(null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!password) {
      setError('Please enter your password.')
      return
    }
    setLoading(true)
    try {
      // Attempt real API login
      const user = await login(email, password)
      if (user.role === 'borrower') {
        router.push('/borrower')
      } else {
        router.push('/lender')
      }
    } catch (err: any) {
      setError(err?.detail || 'Unable to sign in. Check your credentials and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Left brand panel */}
      <div className="relative hidden flex-col justify-between bg-navy p-12 text-white lg:flex">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ScanLine className="size-4.5" aria-hidden />
          </span>
          <span className="text-base font-semibold">MyCreditLens</span>
        </Link>
        <div className="max-w-md">
          <h1 className="text-3xl font-semibold leading-tight text-balance">
            Explainable credit intelligence, under human control.
          </h1>
          <ul className="mt-8 flex flex-col gap-4">
            {[
              { icon: ShieldCheck, text: 'Consent-based, revocable data access' },
              { icon: Eye, text: 'Every score backed by a clear explanation' },
              { icon: Lock, text: 'Tamper-evident audit across all decisions' },
            ].map((f) => (
              <li key={f.text} className="flex items-center gap-3 text-slate-200">
                <f.icon className="size-5 text-primary" aria-hidden />
                {f.text}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-slate-400">
          Academic prototype. Not a certified banking system.
        </p>
      </div>

      {/* Right form */}
      <div className="flex items-center justify-center bg-background p-6">
        <div className="w-full max-w-sm">
          <Link href="/" className="mb-8 flex items-center gap-2 lg:hidden">
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ScanLine className="size-4.5" aria-hidden />
            </span>
            <span className="text-base font-semibold text-navy">MyCreditLens</span>
          </Link>

          <h2 className="text-2xl font-semibold tracking-tight text-navy">
            Sign in to MyCreditLens
          </h2>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Choose your account type to continue.
          </p>

          {/* Role selector */}
          <div
            role="tablist"
            aria-label="Account type"
            className="mt-5 grid grid-cols-2 gap-1 rounded-lg border border-border bg-secondary/60 p-1"
          >
            {(['lender', 'borrower'] as Role[]).map((r) => (
              <button
                key={r}
                type="button"
                role="tab"
                aria-selected={role === r}
                onClick={() => switchRole(r)}
                className={cn(
                  'rounded-md px-3 py-2 text-sm font-medium capitalize transition-colors',
                  role === r
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {r === 'lender' ? 'Lender / Analyst' : 'Borrower'}
              </button>
            ))}
          </div>

          {error && (
            <div
              role="alert"
              className="mt-5 flex items-start gap-2 rounded-lg border border-destructive/25 bg-destructive/5 px-3 py-2.5 text-sm text-destructive"
            >
              <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">
                {role === 'lender' ? 'Work email' : 'Email'}
              </Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={mfaRequired}
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link
                  href="#"
                  className="text-xs font-medium text-primary hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={mfaRequired}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            {mfaRequired && (
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="mfa">Authentication code</Label>
                <Input
                  id="mfa"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="6-digit code"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
                  className="font-mono tracking-widest"
                  autoFocus
                />
                <p className="text-xs text-muted-foreground">
                  MFA is required for privileged lender accounts.
                </p>
              </div>
            )}

            <div className="flex items-center gap-2">
              <Checkbox id="remember" />
              <Label htmlFor="remember" className="text-sm font-normal text-muted-foreground">
                Remember this device
              </Label>
            </div>

            <Button type="submit" size="lg" disabled={loading || authLoading}>
              {loading || authLoading
                ? 'Signing in…'
                : mfaRequired
                  ? 'Verify & Sign In'
                  : role === 'lender'
                    ? 'Continue'
                    : 'Sign In'}
            </Button>
          </form>

          {role === 'lender' && (
            <>
              <div className="my-5 flex items-center gap-3">
                <Separator className="flex-1" />
                <span className="text-xs text-muted-foreground">or</span>
                <Separator className="flex-1" />
              </div>

              <Button variant="outline" size="lg" className="w-full">
                <Building2 className="size-4" />
                Continue with Organisation SSO
              </Button>
            </>
          )}

          <p className="mt-6 text-center text-sm text-muted-foreground">
            {role === 'lender' ? (
              <>
                Are you a borrower?{' '}
                <button
                  type="button"
                  onClick={() => switchRole('borrower')}
                  className="font-medium text-primary hover:underline"
                >
                  Sign in as a borrower
                </button>
              </>
            ) : (
              <>
                Work for a lender?{' '}
                <button
                  type="button"
                  onClick={() => switchRole('lender')}
                  className="font-medium text-primary hover:underline"
                >
                  Sign in to the console
                </button>
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}
