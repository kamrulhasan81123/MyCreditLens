"use client"

import { useMemo, useState } from "react"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { AuditEvent } from "@/lib/types"
import { formatDateTime } from "@/lib/format"

export function AuditTable({ events }: { events: AuditEvent[] }) {
  const [query, setQuery] = useState("")
  const [result, setResult] = useState("ALL")

  const sorted = useMemo(
    () => [...events].sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1)),
    [events],
  )

  const filtered = useMemo(() => {
    return sorted.filter((e) => {
      const q =
        query === "" ||
        e.action.toLowerCase().includes(query.toLowerCase()) ||
        e.user.toLowerCase().includes(query.toLowerCase()) ||
        e.entityId.toLowerCase().includes(query.toLowerCase())
      const r = result === "ALL" || e.result === result
      return q && r
    })
  }, [sorted, query, result])

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by action, user, or entity"
            className="pl-9"
            aria-label="Search audit log"
          />
        </div>
        <Select value={result} onValueChange={(value) => value && setResult(value)}>
          <SelectTrigger className="w-full sm:w-[160px]" aria-label="Filter by result">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All results</SelectItem>
            <SelectItem value="SUCCESS">Success</SelectItem>
            <SelectItem value="FAILURE">Failure</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="overflow-hidden rounded-xl border border-border">
        <Table>
          <TableHeader>
            <TableRow className="bg-secondary/60">
              <TableHead>Timestamp</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>User</TableHead>
              <TableHead>Entity</TableHead>
              <TableHead>IP</TableHead>
              <TableHead>Result</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((e) => (
              <TableRow key={e.id}>
                <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                  {formatDateTime(e.timestamp)}
                </TableCell>
                <TableCell className="text-sm font-medium text-foreground">
                  {e.action.replace(/_/g, " ")}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">{e.user}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {e.entityType} {e.entityId}
                </TableCell>
                <TableCell className="font-mono text-xs text-muted-foreground">{e.ip}</TableCell>
                <TableCell>
                  <span
                    className={
                      e.result === "SUCCESS"
                        ? "text-xs font-medium text-risk-low"
                        : "text-xs font-medium text-risk-high"
                    }
                  >
                    {e.result}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
