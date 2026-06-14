"use client"

import { useCallback, useEffect, useRef, useState } from "react"

const WS_URL  = (process.env.NEXT_PUBLIC_WS_URL  ?? "ws://localhost:8000")  + "/ws"
const API_URL =  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"

export type AgentStatus = "idle" | "listening" | "processing" | "executing"
export type ProviderName = "groq" | "gemini" | "openai" | "custom"

export type Step = {
  action:   string
  keys?:    string[]
  key?:     string
  text?:    string
  seconds?: number
  target?:  string
}

export type TranscriptEntry = {
  id:      number
  hindi:   string
  english: string
  plan:    string
  steps:   Step[]
  success: boolean
  time:    string
}

export type ProviderUsage = {
  requests:             number
  tokens_in:            number
  tokens_out:           number
  daily_request_limit:  number
  usage_pct:            number   // 0-100
}

export type BackendState = {
  status:         AgentStatus
  command_count:  number
  last_hindi:     string
  last_english:   string
  last_plan:      string
  last_steps:     Step[]
  memories:       string[]
  transcript:     TranscriptEntry[]
  provider:       ProviderName
  keys_set:       Record<ProviderName, boolean>
  usage:          Record<ProviderName, ProviderUsage>
}

export type BackendEvent =
  | ({ type: "state" } & BackendState)
  | { type: "status";           status: AgentStatus }
  | { type: "plan";             plan: string; steps: Step[]; requires_confirmation: boolean; usage?: Record<string, ProviderUsage>; provider?: string }
  | { type: "transcript_entry"; entry: TranscriptEntry }
  | { type: "transcript_partial"; english: string }
  | { type: "confirm_required"; plan: string }
  | { type: "done";             plan: string }
  | { type: "verify";           plan: string; action_ids: string[]; steps_count: number; message: string }
  | { type: "undo";             message: string }
  | { type: "aborted";          reason: string }
  | { type: "error";            message: string }
  | { type: "config_changed";   provider: ProviderName; keys_set: Record<string, boolean> }
  | { type: "usage";            data: Record<string, ProviderUsage> }

const DEFAULT_USAGE: ProviderUsage = {
  requests: 0, tokens_in: 0, tokens_out: 0, daily_request_limit: 0, usage_pct: 0,
}

const DEFAULT_STATE: BackendState = {
  status:        "idle",
  command_count:  0,
  last_hindi:    "",
  last_english:  "",
  last_plan:     "",
  last_steps:    [],
  memories:      [],
  transcript:    [],
  provider:      "groq",
  keys_set:      { groq: false, gemini: false, openai: false, custom: false },
  usage: {
    groq:   { ...DEFAULT_USAGE, daily_request_limit: 14400 },
    gemini: { ...DEFAULT_USAGE, daily_request_limit: 1500  },
    openai: { ...DEFAULT_USAGE, daily_request_limit: 999999 },
    custom: { ...DEFAULT_USAGE, daily_request_limit: 999999 },
  },
}

export function useBackend() {
  const [connected,    setConnected]    = useState(false)
  const [backendState, setBackendState] = useState<BackendState>(DEFAULT_STATE)
  const [lastEvent,    setLastEvent]    = useState<BackendEvent | null>(null)
  const wsRef           = useRef<WebSocket | null>(null)
  const reconnectTimer  = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── WebSocket connection ──────────────────────────────────────────────────
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen  = () => { setConnected(true); if (reconnectTimer.current) clearTimeout(reconnectTimer.current) }
    ws.onclose = () => { setConnected(false); reconnectTimer.current = setTimeout(connect, 2000) }
    ws.onerror = () => ws.close()

    ws.onmessage = (e) => {
      try {
        const msg: BackendEvent = JSON.parse(e.data)
        setLastEvent(msg)

        if (msg.type === "state") {
          setBackendState({
            status:        msg.status,
            command_count: msg.command_count,
            last_hindi:    msg.last_hindi,
            last_english:  msg.last_english,
            last_plan:     msg.last_plan,
            last_steps:    msg.last_steps,
            memories:      msg.memories,
            transcript:    msg.transcript,
            provider:      msg.provider,
            keys_set:      msg.keys_set,
            usage:         msg.usage ?? DEFAULT_STATE.usage,
          })
        } else if (msg.type === "status") {
          setBackendState(p => ({ ...p, status: msg.status }))
        } else if (msg.type === "plan") {
          setBackendState(p => ({
            ...p,
            last_plan:  msg.plan,
            last_steps: msg.steps,
            ...(msg.usage    ? { usage:    msg.usage    as any } : {}),
            ...(msg.provider ? { provider: msg.provider as any } : {}),
          }))
        } else if (msg.type === "transcript_entry") {
          setBackendState(p => ({
            ...p,
            transcript:   [...p.transcript, msg.entry],
            last_hindi:   msg.entry.hindi,
            last_english: msg.entry.english,
          }))
        } else if (msg.type === "transcript_partial") {
          setBackendState(p => ({ ...p, last_english: msg.english }))
        } else if (msg.type === "config_changed") {
          setBackendState(p => ({
            ...p,
            provider: msg.provider,
            keys_set: msg.keys_set as any,
          }))
        } else if (msg.type === "usage") {
          setBackendState(p => ({ ...p, usage: msg.data as any }))
        }
      } catch { /* ignore */ }
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  // ── Command helpers ───────────────────────────────────────────────────────
  const send = useCallback((payload: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN)
      wsRef.current.send(JSON.stringify(payload))
  }, [])

  const startListening = useCallback(() => send({ command: "start" }), [send])
  const stopListening  = useCallback(() => send({ command: "stop"  }), [send])
  const triggerUndo    = useCallback(() => send({ command: "undo"  }), [send])

  const setProvider = useCallback((provider: ProviderName) => {
    send({ command: "set_provider", provider })
  }, [send])

  const setApiKey = useCallback((provider: ProviderName, key: string) => {
    send({ command: "set_key", provider, key })
  }, [send])

  const setCustomProvider = useCallback((url: string, model: string, key: string) => {
    send({ command: "set_custom", url, model, key })
  }, [send])

  const refreshUsage = useCallback(() => {
    send({ command: "get_usage" })
  }, [send])

  return {
    connected,
    state: backendState,
    lastEvent,
    startListening,
    stopListening,
    triggerUndo,
    setProvider,
    setApiKey,
    setCustomProvider,
    refreshUsage,
  }
}
