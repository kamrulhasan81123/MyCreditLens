"use client"

import { useCallback, useEffect, useState } from "react"
import { Loader2, ShieldCheck } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { applicationsApi, consentsApi, type ApiError } from "@/lib/api-client"
import { formatDate } from "@/lib/format"

interface ConsentDto {
  id: string
  data_source_type: string
  granted: boolean
  granted_at: string | null
  revoked_at: string | null
  consent_version: string | null
}

export default function ConsentPage() {
  const [applicationId, setApplicationId] = useState<string | null>(null)
  const [consents, setConsents] = useState<ConsentDto[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const applications = await applicationsApi.list({ page_size: 1 })
      const id = applications.items[0]?.id ?? null
      setApplicationId(id)
      setConsents(id ? await consentsApi.list(id) : [])
    } catch (caught) {
      setError((caught as ApiError).detail || "Unable to load consent records")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  async function revoke(consentId: string) {
    if (!applicationId) return
    try {
      await consentsApi.revoke(applicationId, consentId)
      toast.success("Consent revoked")
      await load()
    } catch (caught) {
      toast.error((caught as ApiError).detail || "Consent could not be revoked")
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1"><h1 className="text-2xl font-semibold">Consent</h1><p className="text-sm text-muted-foreground">Permissions recorded for your latest application.</p></div>
      <Card className="border-primary/30 bg-primary/5"><CardContent className="flex items-start gap-3 py-4"><ShieldCheck className="mt-0.5 size-5 text-primary" /><p className="text-sm">Revoking consent prevents future use and uploads for that data source.</p></CardContent></Card>
      {loading ? <div className="flex justify-center py-10"><Loader2 className="size-6 animate-spin" /></div> : null}
      {error ? <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">{error}</div> : null}
      {!loading && !error && consents.length === 0 ? <p className="text-sm text-muted-foreground">No consent records are available.</p> : null}
      <div className="space-y-3">
        {consents.map((consent) => <Card key={consent.id}><CardContent className="flex items-center justify-between gap-4 py-4"><div><p className="text-sm font-medium capitalize">{consent.data_source_type.replaceAll("_", " ")}</p><p className="text-xs text-muted-foreground">{consent.granted ? `Granted ${consent.granted_at ? formatDate(consent.granted_at) : ""}` : `Revoked ${consent.revoked_at ? formatDate(consent.revoked_at) : ""}`}</p></div>{consent.granted ? <Button variant="outline" size="sm" onClick={() => revoke(consent.id)}>Revoke</Button> : <span className="text-xs text-muted-foreground">Revoked</span>}</CardContent></Card>)}
      </div>
    </div>
  )
}
