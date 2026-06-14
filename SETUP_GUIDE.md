# 🛠️ OFFICE-NATOR — Setup Guide

Complete local development and deployment guide.

---

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend runtimes |
| npm | 9+ | Package manager |
| Git | any | Version control |
| Windows | 10/11 | Required for PyAutoGUI desktop control |
| Microphone | any | Voice input |
| Microsoft Excel | any | Target application |

> ⚠️ **Windows only.** PyAutoGUI, PyAudio, and the keyboard library require Windows for full desktop automation. The web dashboards run on any OS.

---

## API Keys Required

Get these before starting:

| Key | Where to get | Free tier |
|---|---|---|
| `SARVAM_API_KEY` | [dashboard.sarvam.ai](https://dashboard.sarvam.ai) | Yes |
| `GROQ_API_KEY` | [console.groq.com/keys](https://console.groq.com/keys) | Yes — 14,400 req/day |
| `GEMINI_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Yes — fallback |

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/srikanth02108/sutra.git
cd sutra
```

### Step 2 — Python virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
```

> **If PyAudio fails on Windows:**
> ```powershell
> pip install pipwin
> pipwin install pyaudio
> ```

> **Torch (large download ~2GB):**
> ```powershell
> pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
> ```
> The Silero VAD model downloads automatically on first run (~10MB from GitHub).

### Step 3 — Configure environment variables

```powershell
copy .env.example .env
```

Edit `.env`:

```env
# ── Required ──────────────────────────────────────────────────────
SARVAM_API_KEY=sk_your_key_here
GROQ_API_KEY=gsk_your_key_here

# ── Optional fallback ─────────────────────────────────────────────
GEMINI_API_KEY=your_gemini_key_here

# ── LLM provider: "groq" (recommended) or "gemini" ───────────────
LLM_PROVIDER=groq

# ── n8n (optional — Groq direct is used by default) ──────────────
N8N_WEBHOOK_URL=http://localhost:5678/webhook/sutra
```

### Step 4 — Frontend (main dashboard)

```powershell
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_LANDING_URL=http://localhost:4000
```

### Step 5 — Landing page

```powershell
cd "landing page"
npm install
```

Create `landing page/.env.local`:

```env
NEXT_PUBLIC_MAIN_APP_URL=http://localhost:3000
```

---

## Running the Full Stack

Open **4 terminal windows**:

### Terminal 1 — Python Backend

```powershell
cd sutra
.\venv\Scripts\Activate
python server.py
```

Expected output:
```
✅ VoiceListener (Silero VAD)
✅ SarvamSTT
✅ Brain (groq)
✅ Actuator
✅ TTSSpeaker
✅ Memory (0 facts)
🚀 Ready — http://localhost:8000  |  ws://localhost:8000/ws
```

### Terminal 2 — Global Hotkey Tray

```powershell
cd sutra
.\venv\Scripts\Activate
python hotkey_tray.py
```

Look for the OFFICE-NATOR icon in your Windows system tray (bottom-right).

### Terminal 3 — Landing Page

```powershell
cd "sutra\landing page"
npm run dev -- --port 4000
```

Opens at `http://localhost:4000`

### Terminal 4 — Main Dashboard

```powershell
cd sutra\frontend
npm run dev
```

Opens at `http://localhost:3000`

---

## Usage

1. Open **Microsoft Excel** and click inside a cell
2. Press **`Alt+.`** (Alt + period) from anywhere
3. Speak your command in **Hindi or Marathi**
4. Watch the action execute and see the verification popup

### Voice command examples

```
"is cell ko bold karo"          → Ctrl+B
"font size 16 set karo"         → Set font size to 16
"column width autofit karo"     → AutoFit column
"borders sab taraf lagao"       → All borders
"merge karke center karo"       → Merge & Center
"pehli row freeze karo"         → Freeze top row
"sort A se Z karo"              → Sort ascending
"undo karo"                     → Ctrl+Z
"save karo"                     → Ctrl+S
```

---

## Smoke Tests

Run these to verify individual components:

```powershell
# Test TTS (should speak English + Hindi greeting)
.\venv\Scripts\python.exe -m voice.tts_speaker

# Test actuator (opens Notepad, types "Hello from Sutra!")
.\venv\Scripts\python.exe -m hands.actuator

# Test brain (requires Groq key in .env)
.\venv\Scripts\python.exe -m brain.n8n_client

# Verify all 129 Excel actions produce correct steps
.\venv\Scripts\python.exe verify_setup.py
```

---

## Deployment

### Frontend & Landing Page → Vercel (free)

Both Next.js apps deploy to Vercel for free.

**Landing page:**
1. [vercel.com/new](https://vercel.com/new) → Import `sutra` repo
2. **Root Directory:** `landing page`
3. Add env var: `NEXT_PUBLIC_MAIN_APP_URL=https://your-dashboard.vercel.app`

**Main dashboard:**
1. Add another project on Vercel → same repo
2. **Root Directory:** `frontend`
3. Add env vars:
   ```
   NEXT_PUBLIC_BACKEND_URL=https://your-ngrok-url.ngrok.io
   NEXT_PUBLIC_WS_URL=wss://your-ngrok-url.ngrok.io
   NEXT_PUBLIC_LANDING_URL=https://officenator.vercel.app
   ```

### Backend → Must run locally (use ngrok to expose)

The Python backend requires a physical Windows machine (microphone, PyAutoGUI, audio playback). It **cannot** be deployed to cloud containers.

**Bridge local backend to deployed frontend using ngrok:**

```powershell
# Install ngrok (one-time)
winget install ngrok.ngrok

# Authenticate (one-time)
ngrok config add-authtoken YOUR_TOKEN

# Every session — expose your local backend
ngrok http 8000
# → Gives you: https://abc123.ngrok-free.app
```

Update your Vercel frontend env vars with the ngrok URL. The backend stays on your machine; the UI is live on the internet.

> **ngrok free tier:** URLs change every session. For a stable URL, upgrade to ngrok Pro ($8/mo) or use a static domain.

---

## MongoDB Atlas (Currently Disabled)

The project includes MongoDB Atlas auth (`landing page/lib/mongodb.ts`, `landing page/app/api/auth/`).

**Why it's disabled:** Node.js on some Windows setups uses `127.0.0.1` as its DNS resolver, which cannot resolve MongoDB Atlas SRV records (`_mongodb._tcp.cluster0...`). This causes `querySrv ECONNREFUSED` errors even when the Atlas cluster is healthy and IP-whitelisted.

**Workaround if you want to re-enable it:**
```typescript
// Add to top of landing page/lib/mongodb.ts
import dns from 'dns'
dns.setServers(['8.8.8.8', '8.8.4.4', '1.1.1.1'])
```

Then set in `landing page/.env.local`:
```env
MONGODB_URI=mongodb+srv://user:pass@cluster0.xxxx.mongodb.net/officenator
JWT_SECRET=your-64-char-hex-secret
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: packaging` | `pip install packaging` |
| `querySrv ECONNREFUSED` (MongoDB) | See MongoDB Atlas section above |
| Groq 429 rate limit | Wait 1 min or switch to Gemini in provider panel |
| VAD model download fails | Check internet connection (downloads from GitHub on first run) |
| `FAILSAFE triggered` | Mouse moved to screen corner — move away and retry |
| Excel not responding | Ensure Excel window is focused before speaking |
| Frontend can't connect | Verify `server.py` is running on port 8000 |
