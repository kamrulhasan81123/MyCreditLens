import { PageHeader } from "@/components/layout/page-header"
import { SettingsForm } from "@/components/lender/settings-form"

export default function SettingsPage() {
  return (
    <div className="space-y-8">
      <PageHeader title="Settings" description="Configure organization details and decision policy." />
      <SettingsForm />
    </div>
  )
}
