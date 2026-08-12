import { BorrowerShell } from "@/components/layout/borrower-shell"
import { RoleGuard } from "@/components/auth/role-guard"

export default function BorrowerLayout({ children }: { children: React.ReactNode }) {
  return (
    <RoleGuard allowed={["borrower"]}>
      <BorrowerShell>{children}</BorrowerShell>
    </RoleGuard>
  )
}
