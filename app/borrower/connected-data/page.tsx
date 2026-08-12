"use client"

import { useCallback, useEffect, useState } from "react"
import { Loader2, Upload } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { applicationsApi, dataSourcesApi, type ApiError } from "@/lib/api-client"

interface DataSourceDto {
  id: string
  source_type: string
  file_name: string | null
  validation_status: string
  record_count: number | null
  reliability_score: number | null
}

export default function ConnectedDataPage() {
  const [applicationId, setApplicationId] = useState<string | null>(null)
  const [sources, setSources] = useState<DataSourceDto[]>([])
  const [sourceType, setSourceType] = useState("bank_statement")
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const applications = await applicationsApi.list({ page_size: 1 })
      const id = applications.items[0]?.id ?? null
      setApplicationId(id)
      setSources(id ? await dataSourcesApi.list(id) : [])
      setError(null)
    } catch (caught) {
      setError((caught as ApiError).detail || "Unable to load connected data")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  async function upload() {
    if (!applicationId || !file) return
    setUploading(true)
    try {
      await dataSourcesApi.upload(applicationId, file, sourceType)
      toast.success("Data source uploaded")
      setFile(null)
      await load()
    } catch (caught) {
      toast.error((caught as ApiError).detail || "Upload failed")
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1"><h1 className="text-2xl font-semibold">Connected data</h1><p className="text-sm text-muted-foreground">Upload UTF-8 CSV transaction data for your latest application.</p></div>
      {loading ? <div className="flex justify-center py-10"><Loader2 className="size-6 animate-spin" /></div> : null}
      {error ? <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">{error}</div> : null}
      {!loading && !applicationId ? <p className="text-sm text-muted-foreground">Create an application before connecting data.</p> : null}
      {applicationId ? <Card><CardContent className="grid gap-4 py-5 sm:grid-cols-[180px_1fr_auto] sm:items-end"><div className="space-y-2"><Label>Source type</Label><Select value={sourceType} onValueChange={(value) => value && setSourceType(value)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="bank_statement">Bank statement</SelectItem><SelectItem value="transaction_csv">Transaction export</SelectItem><SelectItem value="payslip">Payslip CSV</SelectItem><SelectItem value="tax_return">Tax return CSV</SelectItem></SelectContent></Select></div><div className="space-y-2"><Label htmlFor="data-file">CSV file</Label><Input id="data-file" type="file" accept=".csv,.tsv,text/csv" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></div><Button onClick={upload} disabled={!file || uploading}>{uploading ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}Upload</Button></CardContent></Card> : null}
      <div className="space-y-3">{sources.map((source) => <Card key={source.id}><CardContent className="flex items-center justify-between gap-4 py-4"><div><p className="text-sm font-medium">{source.file_name || source.source_type}</p><p className="text-xs text-muted-foreground">{source.record_count ?? 0} records / reliability {Math.round((source.reliability_score ?? 0) * 100)}%</p></div><span className="text-xs font-medium capitalize">{source.validation_status.replaceAll("_", " ")}</span></CardContent></Card>)}</div>
    </div>
  )
}
