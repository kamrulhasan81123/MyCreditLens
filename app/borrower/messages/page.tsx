"use client"

import { useState } from "react"
import { Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

interface Message {
  id: string
  from: "lender" | "borrower"
  author: string
  text: string
  time: string
}

const SEED: Message[] = [
  {
    id: "m1",
    from: "lender",
    author: "Daniel Tan · Analyst",
    text: "Hi Nurul, thanks for your application. Your utility bill scan is a little blurry — could you re-upload a clearer copy?",
    time: "09:20",
  },
  {
    id: "m2",
    from: "borrower",
    author: "You",
    text: "Sure, I'll upload it again now.",
    time: "09:24",
  },
  {
    id: "m3",
    from: "lender",
    author: "Daniel Tan · Analyst",
    text: "Received, thank you. We'll continue the review and update you soon.",
    time: "09:31",
  },
]

export default function MessagesPage() {
  const [messages, setMessages] = useState<Message[]>(SEED)
  const [draft, setDraft] = useState("")

  function send(e: React.FormEvent) {
    e.preventDefault()
    if (draft.trim() === "") return
    setMessages((prev) => [
      ...prev,
      {
        id: `m${prev.length + 1}`,
        from: "borrower",
        author: "You",
        text: draft.trim(),
        time: new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }),
      },
    ])
    setDraft("")
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-9rem)] max-w-2xl flex-col space-y-4">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Messages</h1>
        <p className="text-sm text-muted-foreground">Chat securely with your credit analyst.</p>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardContent className="flex flex-1 flex-col gap-4 overflow-y-auto py-4">
          {messages.map((m) => (
            <div
              key={m.id}
              className={cn("flex flex-col gap-1", m.from === "borrower" ? "items-end" : "items-start")}
            >
              <span className="text-xs text-muted-foreground">{m.author}</span>
              <div
                className={cn(
                  "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                  m.from === "borrower"
                    ? "rounded-br-sm bg-primary text-primary-foreground"
                    : "rounded-bl-sm bg-secondary text-secondary-foreground",
                )}
              >
                {m.text}
              </div>
              <span className="text-[11px] text-muted-foreground">{m.time}</span>
            </div>
          ))}
        </CardContent>
        <form onSubmit={send} className="flex items-center gap-2 border-t border-border p-3">
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Type a message…"
            aria-label="Message"
          />
          <Button type="submit" size="icon" aria-label="Send message">
            <Send className="size-4" />
          </Button>
        </form>
      </Card>
    </div>
  )
}
