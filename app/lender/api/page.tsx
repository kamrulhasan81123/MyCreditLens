import { KeyRound } from "lucide-react"

import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent } from "@/components/ui/card"

export default function ApiPage() {
  return <div className="space-y-8"><PageHeader title="API and integrations" description="Programmatic integration settings." /><Card><CardContent className="flex items-start gap-3 py-6"><KeyRound className="mt-0.5 size-5 text-muted-foreground" /><div><p className="text-sm font-medium">API key management is not enabled</p><p className="mt-1 text-sm text-muted-foreground">Use authenticated FastAPI sessions for this MVP. No example production keys, live endpoints, or webhooks are fabricated in the interface.</p></div></CardContent></Card></div>
}
