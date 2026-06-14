<div align="center">

# 🤖 OFFICE-NATOR

### *The beginning of the Terminator era for your office tools*

**Voice-controlled AI desktop automation. Speak in Hindi, Telugu, Tamil, Marathi(any indian regional language). Watch Excel obey.**

[![License: MIT](https://img.shields.io/badge/License-MIT-cyan.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green.svg)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange.svg)](https://groq.com)
[![Sarvam AI](https://img.shields.io/badge/Sarvam_AI-STT-purple.svg)](https://sarvam.ai)
[![Silero VAD](https://img.shields.io/badge/Silero-VAD-yellow.svg)](https://github.com/snakers4/silero-vad)
[![Built for Bharat](https://img.shields.io/badge/Built_for-Bharat-FF9933.svg)](https://en.wikipedia.org/wiki/India)

---

> 🎤 **"Column ki width autofit karo"** → Excel column auto-fits instantly  
> 🎤 **"Font size 16 set karo"** → Font changes to 16pt  
> 🎤 **"Merge karke center karo"** → Cells merge and center  
> 🎤 **"Borders sab taraf lagao"** → All borders applied  

*No mouse. No keyboard. No English required.*

</div>

---

## 🎬 Demo

> 📹 **[Watch the Demo Video](https://youtube.com) ← Insert link here**

```
┌─────────────────── OFFICE-NATOR Dashboard ────────────────────────┐
│  🎤 Listening...                                                   │
│  ─────────────────────────────────────────────────────────────    │
│  [19:42:11] Heard: "header ko bold aur 16 size karo"              │
│  [19:42:12] Plan:  Bold + set font size to 16                      │
│  [19:42:12] Steps: hotkey ctrl+b → ribbon alt+h fs → type 16      │
│  [19:42:13] ✓ Done!                                                │
│                                                                    │
│  Provider: Groq · 3 req today · 0.0% of 14,400/day limit          │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 The Problem

Office tools like Microsoft Excel are powerful — but only for those who can navigate them fluently in English with a mouse and keyboard. Over **500 million** regional language speakers in India spend 2-3 hours daily on repetitive formatting, navigation, and data tasks — tasks that should take seconds.

**The gap:** No voice interface exists for desktop productivity tools in Indian regional languages.

## ✅ The Solution

OFFICE-NATOR bridges that gap. It is a **voice-first desktop automation agent** that:

1. **Listens** via a global hotkey (`Alt+.`) anywhere on your machine — even when Excel is focused
2. **Understands** Hindi and Marathi speech via Sarvam AI's `saaras:v3` STT model
3. **Plans** using an LLM (Groq Llama 3.3 70B) that classifies intent against a **129-action pre-coded library** — zero hallucination on key sequences
4. **Executes** via PyAutoGUI with human-like mouse movement and keystroke timing
5. **Confirms** destructive actions with voice ("Haan/Nahi") and shows a verification popup

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        OFFICE-NATOR Pipeline                       │
│                                                                    │
│  Alt+. ──► [Silero VAD]──► [Sarvam STT]──► [Memory Context]       │
│              PyAudio         Hindi→EN          Local JSON          │
│                                  │                                 │
│                                  ▼                                 │
│                          [Groq LLM Brain]                          │
│                        Intent Classification                        │
│                       (picks action_id only)                       │
│                                  │                                 │
│                                  ▼                                 │
│                     [Excel Action Library]                         │
│                      129 pre-coded actions                         │
│                       zero hallucination                           │
│                                  │                                 │
│                                  ▼                                 │
│                        [PyAutoGUI Executor]                        │
│                    hotkey / ribbon / type_text                     │
│                                  │                                 │
│                                  ▼                                 │
│                         ✅ Excel responds                           │
│                                                                    │
│  ◄──────── WebSocket ─── [FastAPI Server] ──► [Next.js Dashboard] │
│             Real-time state sync                Web UI + controls  │
└────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Core Features

- 🎤 **Voice in any Indian language** — Hindi, Marathi, and more via Sarvam AI `saaras:v3`
- ⚡ **129 deterministic Excel actions** — every operation is pre-coded Python; the LLM only classifies intent, never invents key sequences
- 🌐 **Real-time web dashboard** — live transcript, execution plan viewer, memory panel
- 🧠 **Stateful memory** — learns your preferences (fonts, styles, habits) across sessions in local JSON
- 🔑 **Global hotkey** — `Alt+.` triggers from anywhere, even when Excel is focused full-screen
- 🔀 **Multi-provider brain** — switch between Groq, Gemini, OpenAI, or any custom OpenAI-compatible endpoint live from the UI
- 📊 **Live usage meter** — tracks tokens and requests per provider against daily free-tier limits
- 🛡️ **Confirmation guard** — destructive actions (delete row, merge cells) always ask "Haan/Nahi" first
- 🔌 **Custom provider support** — point to any Ollama, Together.ai, or Mistral endpoint
- 🖥️ **System tray app** — background hotkey process shows agent state via icon color

---

## 🗂️ Repository Structure

```
sutra/
├── server.py              ← FastAPI backend — WebSocket + REST API
├── main.py                ← CLI-only orchestration loop (no web)
├── hotkey_tray.py         ← Windows system tray + global Alt+. hotkey
├── excel_actions.py       ← 129 pre-coded Excel actions library
├── config.py              ← Centralized config (loads from .env)
├── EXCEL_ACTIONS.md       ← Full reference of all 129 actions
│
├── brain/
│   └── n8n_client.py      ← LLM intent classifier (Groq/Gemini/OpenAI)
├── ears/
│   ├── vad_listener.py    ← Silero VAD push-to-talk listener
│   └── sarvam_stt.py      ← Sarvam AI speech-to-text client
├── hands/
│   └── actuator.py        ← PyAutoGUI executor (hotkey/ribbon/type)
├── voice/
│   └── tts_speaker.py     ← edge-tts text-to-speech output
├── memory/
│   └── mem0_manager.py    ← Local JSON preference memory
│
├── frontend/              ← Next.js 16 dashboard (port 3000)
│   ├── app/
│   ├── components/
│   │   ├── dashboard.tsx
│   │   ├── voice-interface.tsx
│   │   ├── agent-brain.tsx
│   │   ├── transcript-terminal.tsx
│   │   └── provider-panel.tsx
│   └── lib/
│       ├── useBackend.ts
│       └── useSession.ts
│
├── landing page/          ← Next.js 16 landing/marketing site (port 4000)
│   ├── app/
│   │   ├── login/
│   │   └── register/
│   └── components/
│       ├── sections/      ← Hero, Problem, Features, Architecture...
│       └── auth/          ← Login/Register forms
│
└── n8n_workflow/
    └── sutra_workflow.json ← Importable n8n workflow (optional)
```

---

## 🚀 Quick Start

See **[SETUP_GUIDE.md](SETUP_GUIDE.md)** for full instructions. The short version:

```bash
# 1. Clone
git clone https://github.com/srikanth02108/sutra.git
cd sutra

# 2. Python env
python -m venv venv && venv\Scripts\Activate
pip install -r requirements.txt

# 3. Configure keys
cp .env.example .env   # fill in SARVAM_API_KEY, GROQ_API_KEY

# 4. Run (4 terminals)
python server.py                    # Terminal 1 — backend
python hotkey_tray.py               # Terminal 2 — hotkey tray
cd "landing page" && npm run dev -- --port 4000   # Terminal 3
cd frontend && npm run dev          # Terminal 4
```

Open `http://localhost:4000` → Demo Login → `http://localhost:3000`

Press **Alt+.** anywhere to start speaking.

---

## 🧪 Supported Excel Operations

See **[EXCEL_ACTIONS.md](EXCEL_ACTIONS.md)** for the complete 129-action reference.

| Category | Count | Examples |
|---|---|---|
| Formatting | 9 | Bold, italic, underline, clear |
| Font | 7 | Size, family, color |
| Alignment | 11 | Center, wrap text, merge |
| Borders | 11 | All, outside, thick, none |
| Number Format | 8 | Currency, %, date, time |
| Column/Row Size | 11 | AutoFit, set exact width/height |
| Insert/Delete | 8 | Row, column, cells |
| Editing | 22 | Undo, paste values, fill down |
| Navigation | 9 | Go to cell, A1, next sheet |
| Data | 11 | Sort, filter, remove duplicates |
| Insert Objects | 11 | Chart, pivot, table, hyperlink |
| View | 10 | Freeze, zoom, split |
| + more | 11 | Page layout, formulas, review |

---

## ⚠️ Known Limitations & Architecture Notes

### MongoDB Atlas — Commented Out

The project includes a MongoDB Atlas integration (`landing page/lib/mongodb.ts`, `landing page/app/api/auth/`) for persistent user accounts. This is **currently commented out** due to a DNS SRV resolution issue specific to Windows environments where Node.js resolves DNS via `127.0.0.1` (loopback) instead of the system DNS, causing `querySrv ECONNREFUSED` errors against Atlas hostnames.

**Status:** The auth routes exist and are correct. To re-enable:
1. Add `dns.setServers(['8.8.8.8', '8.8.4.4'])` at the top of `lib/mongodb.ts`
2. Set `MONGODB_URI`, `JWT_SECRET` in `landing page/.env.local`
3. The login/register forms currently redirect directly without DB validation

### Why the Backend Must Run Locally

The Python backend (`server.py`) uses:
- **PyAudio** — direct microphone access (not available in cloud containers)
- **PyAutoGUI** — sends keyboard/mouse events to the local desktop
- **Silero VAD** — real-time audio processing
- **edge-tts** — audio playback through local speakers

These require a **physical Windows machine**. The backend cannot be hosted on Vercel, Railway, or any containerized platform. See [SETUP_GUIDE.md](SETUP_GUIDE.md#deployment) for the ngrok bridging approach.

---

## 👥 Contributors

| Name | Role | GitHub |
|---|---|---|
| Kuldeep Reddy | Lead Developer | [@23wj1a0541](https://github.com/23wj1a0541) |
| Srikanth | Developer | [@srikanth02108](https://github.com/srikanth02108) |

*Want to contribute? See [CONTRIBUTING.md](CONTRIBUTING.md)*

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

**Built for Bharat 🇮🇳 · Made with 🤖 + voice**

*"The best interface is no interface — just your voice in your language."*

</div>
