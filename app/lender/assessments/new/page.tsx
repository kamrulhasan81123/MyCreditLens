import { PageHeader } from "@/components/layout/page-header"
import { AssessmentWizard } from "@/components/lender/assessment-wizard"

export default function NewAssessmentPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="New assessment"
        description="Create a credit assessment from alternative data with borrower consent."
      />
      <AssessmentWizard />
    </div>
  )
}
