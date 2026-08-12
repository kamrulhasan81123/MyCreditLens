"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { authApi, borrowersApi, type ApiError } from "@/lib/api-client"

export default function ProfilePage() {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [address, setAddress] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([authApi.me(), borrowersApi.me()]).then(([user, borrower]) => {
      setName(user.full_name)
      setEmail(user.email)
      setPhone(borrower.phone ?? "")
      setAddress(borrower.address ?? "")
    }).catch((error: ApiError) => toast.error(error.detail || "Unable to load profile")).finally(() => setLoading(false))
  }, [])

  async function save() {
    setSaving(true)
    try {
      await borrowersApi.updateMe({ phone, address })
      toast.success("Profile updated")
    } catch (error) {
      toast.error((error as ApiError).detail || "Profile could not be updated")
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="flex min-h-64 items-center justify-center"><Loader2 className="size-6 animate-spin" /></div>
  return <div className="space-y-6"><div><h1 className="text-2xl font-semibold">Profile</h1><p className="text-sm text-muted-foreground">Manage your borrower contact information.</p></div><Card><CardHeader><CardTitle>Personal details</CardTitle><CardDescription>Name and email changes require account administration.</CardDescription></CardHeader><CardContent className="grid gap-4 sm:grid-cols-2"><div className="space-y-2"><Label htmlFor="name">Full name</Label><Input id="name" value={name} disabled /></div><div className="space-y-2"><Label htmlFor="email">Email</Label><Input id="email" value={email} disabled /></div><div className="space-y-2"><Label htmlFor="phone">Phone</Label><Input id="phone" value={phone} onChange={(event) => setPhone(event.target.value)} /></div><div className="space-y-2"><Label htmlFor="address">Address</Label><Input id="address" value={address} onChange={(event) => setAddress(event.target.value)} /></div></CardContent></Card><div className="flex justify-end"><Button onClick={save} disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : null}Save changes</Button></div></div>
}
