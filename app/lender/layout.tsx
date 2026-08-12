import { LenderShell } from '@/components/layout/lender-shell'
import { RoleGuard } from '@/components/auth/role-guard'

export default function LenderLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <RoleGuard allowed={["admin", "credit_analyst", "compliance_reviewer"]}>
      <LenderShell>{children}</LenderShell>
    </RoleGuard>
  )
}
