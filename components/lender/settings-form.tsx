"use client"

import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export function SettingsForm() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Organization</CardTitle>
          <CardDescription>Details shown across the lender console.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="org">Organization name</Label>
            <Input id="org" defaultValue="Nusantara Microfinance" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="reg">Regulator ID</Label>
            <Input id="reg" defaultValue="BNM-MFI-0421" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="currency">Base currency</Label>
            <Select defaultValue="MYR">
              <SelectTrigger id="currency">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="MYR">MYR — Malaysian Ringgit</SelectItem>
                <SelectItem value="IDR">IDR — Indonesian Rupiah</SelectItem>
                <SelectItem value="PHP">PHP — Philippine Peso</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="tz">Timezone</Label>
            <Select defaultValue="MYT">
              <SelectTrigger id="tz">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="MYT">Asia/Kuala_Lumpur (MYT)</SelectItem>
                <SelectItem value="WIB">Asia/Jakarta (WIB)</SelectItem>
                <SelectItem value="PHT">Asia/Manila (PHT)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Decision policy</CardTitle>
          <CardDescription>Thresholds and controls for automated recommendations.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="low">Low-risk PD ceiling</Label>
              <Input id="low" type="number" step="0.01" defaultValue="0.15" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="high">High-risk PD floor</Label>
              <Input id="high" type="number" step="0.01" defaultValue="0.30" />
            </div>
          </div>
          <Separator />
          <ToggleRow
            title="Require rationale on overrides"
            description="Analysts must document a reason when overriding the model recommendation."
            defaultChecked
          />
          <ToggleRow
            title="Auto-approve low-risk applications"
            description="Automatically approve applications below the low-risk PD ceiling that pass all policy rules."
          />
          <ToggleRow
            title="Human review for automated declines"
            description="Route every automated decline to an analyst before it is finalized."
            defaultChecked
          />
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={() => toast.success("Settings saved")}>Save changes</Button>
      </div>
    </div>
  )
}

function ToggleRow({
  title,
  description,
  defaultChecked,
}: {
  title: string
  description: string
  defaultChecked?: boolean
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="space-y-0.5">
        <p className="text-sm font-medium text-foreground">{title}</p>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <Switch defaultChecked={defaultChecked} />
    </div>
  )
}
