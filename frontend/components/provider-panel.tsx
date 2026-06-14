"use client"

import { useEffect, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { motion, AnimatePresence } from "framer-motion"
import { Zap, Eye, EyeOff, Check, ChevronDown, Plus, X } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ProviderName, ProviderUsage } from "@/lib/useBackend"

const PROVIDERS: {
  id: ProviderName
  label: string
  model: string
  limit: string
  color: string
}[] = [
  { id: "groq",   label: "Groq",   model: "Llama 3.3 70B",    limit: "14,400 req/day", color: "text-chart-4" },
  { id: "gemini", label: "Gemini", model: "2.5 Flash",         limit: "1,500 req/day",  color: "text-primary" },
  { id: "openai", label: "OpenAI", model: "GPT-4o-mini",       limit: "paid",           color: "text-chart-2" },
  { id: "custom", label: "Custom", model: "OpenAI-compatible", limit: "varies",         color: "text-chart-5" },
]

type Props = {
  provider:      ProviderName
  keysSet:       Record<string, boolean>
  usage:         Record<string, ProviderUsage>
  onSetProvider: (p: ProviderName) => void
  onSetKey:      (p: ProviderName, k: string) => void
  onSetCustom:   (url: string, model: string, key: string) => void
}

// ── Usage bar ─────────────────────────────────────────────────────────────────
function UsageBar({ pct }: { pct: number }) {
  const safe = Math.min(100, Math.max(0, pct))
  const color =
    safe > 80 ? "bg-destructive" : safe > 50 ? "bg-chart-4" : "bg-chart-2"
  return (
    <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-secondary/60">
      <motion.div
        className={cn("h-full rounded-full", color)}
        initial={{ width: 0 }}
        animate={{ width: `${safe}%` }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      />
    </div>
  )
}

// ── API key input ─────────────────────────────────────────────────────────────
function KeyInput({
  label,
  hasKey,
  onSave,
}: {
  label:  string
  hasKey: boolean
  onSave: (k: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const [val, setVal]         = useState("")
  const [show, setShow]       = useState(false)
  const inputRef              = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editing) inputRef.current?.focus()
  }, [editing])

  const commit = () => {
    if (val.trim()) { onSave(val.trim()); setEditing(false); setVal("") }
  }

  if (!editing) {
    return (
      <button
        onClick={e => { e.stopPropagation(); setEditing(true) }}
        className={cn(
          "flex shrink-0 items-center gap-1 rounded-md border px-2 py-1 font-mono text-[10px] uppercase tracking-widest transition-colors",
          hasKey
            ? "border-chart-2/30 bg-chart-2/10 text-chart-2"
            : "border-border bg-secondary/30 text-muted-foreground hover:border-primary/30 hover:text-foreground",
        )}
      >
        {hasKey ? <Check className="h-3 w-3" /> : <Plus className="h-3 w-3" />}
        {hasKey ? "key set" : "add key"}
      </button>
    )
  }

  return (
    <div className="flex w-full items-center gap-1 pt-2" onClick={e => e.stopPropagation()}>
      <div className="relative flex-1">
        <input
          ref={inputRef}
          type={show ? "text" : "password"}
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter")  commit()
            if (e.key === "Escape") { setEditing(false); setVal("") }
          }}
          placeholder={`Paste ${label} API key…`}
          className="w-full rounded-md border border-primary/40 bg-[oklch(0.15_0.012_240)] px-2 py-1.5 font-mono text-[10px] text-foreground outline-none placeholder:text-muted-foreground/60"
        />
        <button
          type="button"
          onClick={() => setShow(s => !s)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          {show ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
        </button>
      </div>
      <button
        onClick={commit}
        className="shrink-0 rounded-md bg-primary/20 px-2 py-1.5 font-mono text-[10px] text-primary hover:bg-primary/30"
      >
        save
      </button>
      <button
        onClick={() => { setEditing(false); setVal("") }}
        className="shrink-0 text-muted-foreground hover:text-foreground"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export function ProviderPanel({
  provider, keysSet, usage,
  onSetProvider, onSetKey, onSetCustom,
}: Props) {
  const [open,        setOpen]        = useState(false)
  const [mounted,     setMounted]     = useState(false)
  const [customUrl,   setCustomUrl]   = useState("")
  const [customModel, setCustomModel] = useState("")
  const [customKey,   setCustomKey]   = useState("")

  const containerRef = useRef<HTMLDivElement>(null)
  const panelRef      = useRef<HTMLDivElement>(null)

  // Only allowed to portal once mounted on the client (avoids SSR mismatch)
  useEffect(() => { setMounted(true) }, [])

  // Close when clicking outside — checks BOTH the trigger and the portaled panel,
  // since the panel is no longer a DOM child of containerRef once portaled
  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      const target = e.target as Node
      const insideTrigger = containerRef.current?.contains(target)
      const insidePanel   = panelRef.current?.contains(target)
      if (!insideTrigger && !insidePanel) setOpen(false)
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [open])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false) }
    document.addEventListener("keydown", handler)
    return () => document.removeEventListener("keydown", handler)
  }, [open])

  const safeKeysSet = keysSet ?? { groq: false, gemini: false, openai: false, custom: false }
  const safeUsage   = usage   ?? {}

  const active      = PROVIDERS.find(p => p.id === provider) ?? PROVIDERS[0]
  const activeUsage = safeUsage[provider] ?? {
    requests: 0, tokens_in: 0, tokens_out: 0, daily_request_limit: 0, usage_pct: 0,
  }

  return (
    // Positioned relative so the dropdown is anchored to this element only
    <div ref={containerRef} className="relative">

      {/* ── Trigger pill ─────────────────────────────────────────────── */}
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
      >
        <Zap className={cn("h-3 w-3", active.color)} />
        <span className={active.color}>{active.label}</span>
        <span className="text-muted-foreground/50">·</span>
        <span>{activeUsage.usage_pct.toFixed(0)}%</span>
        <ChevronDown className={cn("h-3 w-3 transition-transform duration-200", open && "rotate-180")} />
      </button>

      {/* ── Dropdown — rendered via portal to <body> ──────────────────
          This escapes any ancestor with transform/filter/backdrop-filter/
          opacity<1, which would otherwise force `fixed` to be positioned
          relative to (and visually composited with) that ancestor —
          the cause of the "x-ray" / see-through panel. */}
      {mounted && createPortal(
        <AnimatePresence>
          {open && (
            <>
              {/* Dimming backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15, ease: "easeOut" }}
                className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-[2px]"
                onClick={() => setOpen(false)}
              />

              <motion.div
                ref={panelRef}
                initial={{ opacity: 0, y: -6, scale: 0.98 }}
                animate={{ opacity: 1, y: 0,  scale: 1    }}
                exit={{    opacity: 0, y: -6, scale: 0.98 }}
                transition={{ duration: 0.15, ease: "easeOut" }}
                className={cn(
                  "fixed z-[101] isolate w-[22rem] rounded-2xl p-4 shadow-2xl",
                  "border border-border",
                  // position below the trigger — top bar is ~65px tall
                  "top-[68px] right-4",
                )}
                style={{
                  maxHeight: "calc(100vh - 88px)",
                  overflowY: "auto",
                  backgroundColor: "oklch(0.16 0.014 240)",
                  boxShadow: "0 8px 48px -4px rgba(0,0,0,0.85), 0 0 0 1px oklch(0.85 0.05 200 / 15%)",
                }}
              >
                {/* Header row */}
                <div className="mb-3 flex items-center justify-between">
                  <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    Brain Provider
                  </p>
                  <button
                    onClick={() => setOpen(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* Provider cards */}
                <div className="space-y-2">
                  {PROVIDERS.map(p => {
                    const u = safeUsage[p.id] ?? {
                      requests: 0, usage_pct: 0, daily_request_limit: 0,
                      tokens_in: 0, tokens_out: 0,
                    }
                    const isActive  = p.id === provider
                    const hasKey    = safeKeysSet[p.id] ?? false

                    return (
                      <div
                        key={p.id}
                        className={cn(
                          "rounded-xl border p-3 transition-colors",
                          isActive
                            ? "border-primary/40 bg-[oklch(0.22_0.014_240)]"
                            : "border-border bg-[oklch(0.20_0.014_240)] hover:bg-[oklch(0.22_0.014_240)]",
                        )}
                      >
                        {/* Top row — radio + labels + key button */}
                        <div className="flex items-center justify-between gap-2">
                          <button
                            onClick={() => onSetProvider(p.id)}
                            className="flex min-w-0 items-center gap-2"
                          >
                            {/* radio dot */}
                            <span className={cn(
                              "h-2 w-2 shrink-0 rounded-full border-2 transition-colors",
                              isActive
                                ? "border-primary bg-primary"
                                : "border-muted-foreground bg-transparent",
                            )} />
                            <span className={cn("text-sm font-semibold", p.color)}>
                              {p.label}
                            </span>
                            <span className="truncate font-mono text-[9px] text-muted-foreground">
                              {p.model}
                            </span>
                          </button>

                          <KeyInput
                            label={p.label}
                            hasKey={hasKey}
                            onSave={key => onSetKey(p.id, key)}
                          />
                        </div>

                        {/* Usage bar — always shown for active, shown for others if key is set */}
                        {(isActive || hasKey) && (
                          <div className="mt-2">
                            <div className="flex items-center justify-between font-mono text-[9px] text-muted-foreground">
                              <span>{u.requests} req today</span>
                              <span>
                                {u.usage_pct.toFixed(1)}% · {p.limit}
                              </span>
                            </div>
                            <UsageBar pct={u.usage_pct} />
                            {(u.tokens_in + u.tokens_out) > 0 && (
                              <p className="mt-0.5 font-mono text-[9px] text-muted-foreground">
                                {(u.tokens_in + u.tokens_out).toLocaleString()} tokens
                              </p>
                            )}
                          </div>
                        )}

                        {/* Custom provider fields — only when custom is active */}
                        {p.id === "custom" && isActive && (
                          <div className="mt-3 space-y-2 border-t border-border pt-3">
                            <input
                              value={customUrl}
                              onChange={e => setCustomUrl(e.target.value)}
                              placeholder="Base URL  e.g. http://localhost:11434/v1"
                              className="w-full rounded-md border border-border bg-[oklch(0.15_0.012_240)] px-2 py-1.5 font-mono text-[10px] text-foreground outline-none placeholder:text-muted-foreground/60"
                            />
                            <input
                              value={customModel}
                              onChange={e => setCustomModel(e.target.value)}
                              placeholder="Model name  e.g. llama3.2"
                              className="w-full rounded-md border border-border bg-[oklch(0.15_0.012_240)] px-2 py-1.5 font-mono text-[10px] text-foreground outline-none placeholder:text-muted-foreground/60"
                            />
                            <button
                              onClick={() => {
                                if (customUrl && customModel)
                                  onSetCustom(customUrl, customModel, customKey)
                              }}
                              className="w-full rounded-md bg-primary/20 py-1.5 font-mono text-[10px] text-primary hover:bg-primary/30"
                            >
                              apply custom provider
                            </button>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>

                <p className="mt-3 font-mono text-[9px] text-muted-foreground/50">
                  Keys stored in memory only — cleared on server restart.
                </p>
              </motion.div>
            </>
          )}
        </AnimatePresence>,
        document.body
      )}
    </div>
  )
}