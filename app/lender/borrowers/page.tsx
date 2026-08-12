"use client"

import Link from "next/link"
import { Card, CardContent } from "@/components/ui/card"
import { PageHeader } from "@/components/layout/page-header"
import { RiskBadge } from "@/components/risk/badges"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatDate, SEGMENT_LABEL } from "@/lib/format"
import { useBorrowers } from "@/lib/hooks"
import { Loader2 } from "lucide-react"

function initials(name: string) {
  return name
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
}

export default function BorrowersPage() {
  const { borrowers, isLoading, error } = useBorrowers()

  return (
    <div className="space-y-8">
      <PageHeader
        title="Borrowers"
        description="People and businesses assessed with MyCreditLens."
      />
      {isLoading && borrowers.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">Loading borrowers...</span>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}
      {!isLoading && !error ? <Card>
        <CardContent className="p-0">
          <div className="overflow-hidden rounded-xl">
            <Table>
              <TableHeader>
                <TableRow className="bg-secondary/60">
                  <TableHead>Borrower</TableHead>
                  <TableHead>Segment</TableHead>
                  <TableHead className="text-right">Applications</TableHead>
                  <TableHead>Latest risk</TableHead>
                  <TableHead>Active application</TableHead>
                  <TableHead>Last updated</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {borrowers.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="size-8">
                          <AvatarFallback className="bg-secondary text-xs text-secondary-foreground">
                            {initials(b.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="text-sm font-medium text-foreground">{b.name}</p>
                          <p className="text-xs text-muted-foreground">{b.occupation}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {SEGMENT_LABEL[b.segment] || b.segment}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{b.applications}</TableCell>
                    <TableCell>
                      <RiskBadge band={b.latestRiskBand} />
                    </TableCell>
                    <TableCell className="text-sm">
                      {b.activeApplication ? (
                        <Link
                          href={`/lender/applications/${b.activeApplication}`}
                          className="text-primary hover:underline"
                        >
                          {b.activeApplication}
                        </Link>
                      ) : (
                        <span className="text-muted-foreground">None</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(b.lastUpdated)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card> : null}
    </div>
  )
}
