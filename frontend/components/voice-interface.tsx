"use client"

import { Mic } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

export type AgentState = "idle" | "listening" | "processing" | "executing"

const STATUS_COPY: Record<AgentState, string> = {
  idle: "Press Alt+. to speak",
  listening: "Listening...",
  processing: "Translating via Sarvam AI...",
  executing: "Executing UI actions...",
}

export function VoiceInterface({
  state,
  onToggle,
  connected,
  lastEnglish,
}: {
  state: AgentState
  onToggle: () => void
  connected: boolean
  lastEnglish?: string
}) {
  const isListening = state === "listening"
  const isProcessing = state === "processing" || state === "executing"

  return (
    <section className="relative flex flex-1 flex-col items-center justify-center px-6 py-12">
      {/* status pill */}
      <div className="mb-12 flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-xs font-mono uppercase tracking-widest text-muted-foreground">
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            state === "idle" ? "bg-muted-foreground" : "bg-primary",
            state !== "idle" && "animate-pulse",
          )}
        />
        Agent {state === "idle" ? "Standby" : "Active"}
      </div>

      <div className="relative flex h-72 w-72 items-center justify-center sm:h-80 sm:w-80">
        {/* pulsing rings when listening */}
        <AnimatePresence>
          {isListening &&
            [0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="absolute rounded-full border border-primary/40"
                initial={{ width: 160, height: 160, opacity: 0.6 }}
                animate={{ width: 320, height: 320, opacity: 0 }}
                exit={{ opacity: 0 }}
                transition={{
                  duration: 2,
                  repeat: Number.POSITIVE_INFINITY,
                  delay: i * 0.6,
                  ease: "easeOut",
                }}
              />
            ))}
        </AnimatePresence>

        {/* spinning border when processing */}
        {isProcessing && (
          <motion.span
            className="absolute h-60 w-60 rounded-full border-2 border-transparent border-t-primary border-r-primary/50"
            animate={{ rotate: 360 }}
            transition={{
              duration: 1.4,
              repeat: Number.POSITIVE_INFINITY,
              ease: "linear",
            }}
          />
        )}

        {/* idle soft halo */}
        <motion.span
          className="absolute h-56 w-56 rounded-full bg-primary/20 blur-3xl"
          animate={{
            opacity: state === "idle" ? [0.3, 0.55, 0.3] : 0.7,
            scale: state === "idle" ? [1, 1.08, 1] : 1.15,
          }}
          transition={{
            duration: 4,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />

        {/* main button */}
        <motion.button
          type="button"
          onClick={onToggle}
          disabled={!connected}
          whileTap={{ scale: 0.94 }}
          aria-label={isListening ? "Stop listening" : "Start listening"}
          className={cn(
            "glass relative z-10 flex h-44 w-44 items-center justify-center rounded-full",
            "ring-1 ring-primary/40 transition-shadow sm:h-48 sm:w-48",
            !connected && "opacity-40 cursor-not-allowed",
          )}
          style={{
            boxShadow: isListening
              ? "0 0 60px -8px var(--neon), inset 0 0 30px -10px var(--neon)"
              : "0 0 36px -14px var(--neon)",
          }}
        >
          <motion.span
            animate={{ scale: isListening ? [1, 1.12, 1] : 1 }}
            transition={{
              duration: 1.2,
              repeat: isListening ? Number.POSITIVE_INFINITY : 0,
              ease: "easeInOut",
            }}
          >
            <Mic
              className={cn(
                "h-16 w-16 transition-colors",
                state === "idle" ? "text-primary/80" : "text-primary text-glow",
              )}
              strokeWidth={1.5}
            />
          </motion.span>
        </motion.button>
      </div>

      {/* status text */}
      <div className="mt-12 h-8 text-center">
        <AnimatePresence mode="wait">
          <motion.p
            key={state}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
            className="font-mono text-lg tracking-tight text-foreground"
          >
            {!connected ? "Backend offline — start server.py" : STATUS_COPY[state]}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* last heard text */}
      {lastEnglish && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-3 max-w-xs text-balance text-center text-sm text-primary/80 font-mono"
        >
          &ldquo;{lastEnglish}&rdquo;
        </motion.p>
      )}

      <p className="mt-4 max-w-xs text-balance text-center text-xs text-muted-foreground">
        Press <span className="font-mono text-primary">Alt+.</span> anywhere — even when Excel is focused — to speak a command.
      </p>
    </section>
  )
}
