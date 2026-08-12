"use client"

import { useMemo, useState } from "react"
import Link from "next/link"
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
import { RiskBadge, StatusBadge } from "@/components/risk/badges"
import type { Application } from "@/lib/types"
import { formatCurrency, formatDate, formatPercent, SEGMENT_LABEL } from "@/lib/format"

export function ApplicationsTable({ applications }: { applications: Application[] }) {
  const [query, setQuery] = useState("")
  const [risk, setRisk] = useState("ALL")
  const [status, setStatus] = useState("ALL")

  const filtered = useMemo(() => {
    return applications.filter((a) => {
      const matchesQuery =
        query === "" ||
        a.borrowerName.toLowerCase().includes(query.toLowerCase()) ||
        a.id.toLowerCase().includes(query.toLowerCase())
      const matchesRisk = risk === "ALL" || a.riskBand === risk
      const matchesStatus = status === "ALL" || a.status === status
      return matchesQuery && matchesRisk && matchesStatus
    })
  }, [applications, query, risk, status])

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by borrower or application ID"
            className="pl-9"
            aria-label="Search applications"
          />
        </div>
        <Select value={risk} onValueChange={(value) => value && setRisk(value)}>
          <SelectTrigger className="w-full sm:w-[160px]" aria-label="Filter by risk band">
            <SelectValue placeholder="Risk band" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All risk bands</SelectItem>
            <SelectItem value="LOW">Low</SelectItem>
            <SelectItem value="MEDIUM">Medium</SelectItem>
            <SelectItem value="HIGH">High</SelectItem>
          </SelectContent>
        </Select>
        <Select value={status} onValueChange={(value) => value && setStatus(value)}>
          <SelectTrigger className="w-full sm:w-[190px]" aria-label="Filter by status">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All statuses</SelectItem>
            <SelectItem value="SUBMITTED">Submitted</SelectItem>
            <SelectItem value="READY_FOR_SCORING">Ready for Scoring</SelectItem>
            <SelectItem value="SCORED">Scored</SelectItem>
            <SelectItem value="MANUAL_REVIEW">Manual Review</SelectItem>
            <SelectItem value="INFORMATION_REQUESTED">Information Requested</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="overflow-hidden rounded-xl border border-border">
        <Table>
          <TableHeader>
            <TableRow className="bg-secondary/60">
              <TableHead>Application</TableHead>
              <TableHead>Segment</TableHead>
              <TableHead className="text-right">Requested</TableHead>
              <TableHead className="text-right">PD</TableHead>
              <TableHead>Risk</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Analyst</TableHead>
              <TableHead>Updated</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((a) => (
              <TableRow key={a.id} className="cursor-pointer">
                <TableCell>
                  <Link href={`/lender/applications/${a.id}`} className="block">
                    <span className="font-medium text-foreground">{a.borrowerName}</span>
                    <span className="block text-xs text-muted-foreground">{a.id}</span>
                  </Link>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {SEGMENT_LABEL[a.borrowerType]}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatCurrency(a.requestedAmount)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatPercent(a.probabilityOfDefault)}
                </TableCell>
                <TableCell>
                  <RiskBadge band={a.riskBand} />
                </TableCell>
                <TableCell>
                  <StatusBadge status={a.status} />
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">{a.assignedAnalyst}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDate(a.lastUpdated)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {filtered.length === 0 ? (
          <div className="px-4 py-12 text-center text-sm text-muted-foreground">
            No applications match your filters.
          </div>
        ) : null}
      </div>
    </div>
  )
}
