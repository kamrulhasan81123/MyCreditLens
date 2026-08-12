"use client"

import { useEffect } from "react"
import { Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"

import { useAuth } from "@/lib/auth-context"
import type { UserProfile } from "@/lib/api-client"

export function RoleGuard({
  allowed,
  children,
}: {
  allowed: UserProfile["role"][]
  children: React.ReactNode
}) {
  const router = useRouter()
  const { user, isLoading, isAuthenticated } = useAuth()

  useEffect(() => {
    if (isLoading) return
    if (!isAuthenticated || !user) {
      router.replace("/sign-in")
      return
    }
    if (!allowed.includes(user.role)) {
      router.replace(user.role === "borrower" ? "/borrower" : "/lender")
    }
  }, [allowed, isAuthenticated, isLoading, router, user])

  if (isLoading || !user || !allowed.includes(user.role)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Checking access" />
      </div>
    )
  }

  return children
}
