"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { FileText, Loader2, UploadCloud } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { applicationsApi, dataSourcesApi, type ApiError } from "@/lib/api-client"

interface DocumentDto {
  id: string
  file_name: string | null
  source_type: string
  validation_status: string
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentDto[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const applications = await applicationsApi.list({ page_size: 1 })
        const id = applications.items[0]?.id
        setDocuments(id ? await dataSourcesApi.list(id) : [])
      } catch (caught) {
        setError((caught as ApiError).detail || "Unable to load documents")
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div><h1 className="text-2xl font-semibold">Documents</h1><p className="text-sm text-muted-foreground">Files attached to your latest application.</p></div>
        <Button render={<Link href="/borrower/connected-data" />}><UploadCloud className="size-4" />Upload</Button>
      </div>
      {loading ? <div className="flex justify-center py-10"><Loader2 className="size-6 animate-spin" /></div> : null}
      {error ? <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">{error}</div> : null}
      {!loading && !error && documents.length === 0 ? <p className="text-sm text-muted-foreground">No files have been uploaded.</p> : null}
      <div className="space-y-3">
        {documents.map((document) => (
          <Card key={document.id}><CardContent className="flex items-center justify-between py-4"><div className="flex items-center gap-3"><FileText className="size-5 text-muted-foreground" /><div><p className="text-sm font-medium">{document.file_name || document.source_type}</p><p className="text-xs capitalize text-muted-foreground">{document.source_type.replaceAll("_", " ")}</p></div></div><span className="text-xs capitalize">{document.validation_status.replaceAll("_", " ")}</span></CardContent></Card>
        ))}
      </div>
    </div>
  )
}
