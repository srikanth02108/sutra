# 🔐 Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` branch | ✅ Active |
| Older tagged releases | ⚠️ Best effort |

---

## 🚨 Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

A public issue exposes the vulnerability to everyone before a fix is available. Instead, use one of these private channels:

### Option 1 — GitHub Private Security Advisory (preferred)

1. Go to the repository on GitHub
2. Click **Security** tab → **Advisories** → **New draft security advisory**
3. Describe the vulnerability in detail
4. We will respond within **72 hours** and work with you on a coordinated disclosure

### Option 2 — Direct email

📧 Contact the maintainer directly via GitHub profile: [@srikanth02108](https://github.com/srikanth02108)

---

## What to Include in Your Report

A good vulnerability report includes:

- **Description** — what the vulnerability is and where it exists
- **Impact** — what an attacker could achieve by exploiting it
- **Steps to reproduce** — exact commands, requests, or inputs
- **Affected component** — Python backend, Next.js frontend, landing page, etc.
- **Suggested fix** — if you have one (optional but appreciated)

---

## Scope

### In Scope

| Area | Examples |
|---|---|
| **API endpoints** | `/api/auth/register`, `/api/auth/login`, `/api/session` |
| **JWT handling** | Token forgery, secret exposure, improper validation |
| **WebSocket** | Unauthorized command injection via `ws://localhost:8000/ws` |
| **Dependency vulnerabilities** | Known CVEs in `requirements.txt` or `package.json` |
| **Secrets in codebase** | Accidentally committed API keys or credentials |
| **LLM prompt injection** | Crafted voice input that manipulates the LLM into unauthorized actions |

### Out of Scope

- Vulnerabilities in third-party services (Groq, Sarvam AI, Gemini, MongoDB Atlas)
- Issues that require physical access to the target machine
- Self-XSS or issues requiring user interaction to exploit yourself
- Rate limiting on free-tier APIs (this is an upstream provider limitation)
- The fact that PyAutoGUI has full desktop control (this is intentional — it's a desktop automation tool)

---

## ⚠️ Special Security Notes for This Project

### PyAutoGUI — By Design

OFFICE-NATOR uses PyAutoGUI to control the mouse and keyboard. **This is the core feature, not a vulnerability.** The tool requires trust from the user running it. Never run OFFICE-NATOR on a machine you don't own or trust.

### Local-only Architecture

The Python backend (`server.py`) is designed to run locally and binds to `localhost:8000`. It is **not hardened for public internet exposure**. If you use ngrok or any tunneling tool to expose the backend publicly:

- Use ngrok's [IP restrictions](https://ngrok.com/docs/ngrok-agent/config/#ip-restrictions) feature
- Consider adding a bearer token to the FastAPI server
- Never run with sensitive Excel files open unless you trust the network

### API Keys

API keys (`GROQ_API_KEY`, `SARVAM_API_KEY`, `GEMINI_API_KEY`) are stored in `.env` which is gitignored. If you accidentally commit a key:

1. **Immediately revoke it** at the provider's dashboard (Groq console, Sarvam dashboard, Google AI Studio)
2. Generate a new key
3. Run `git filter-branch` or use BFG Repo Cleaner to scrub the key from git history
4. Force push the cleaned history

### MongoDB Atlas (Disabled)

The MongoDB Atlas integration is currently **commented out** due to a local DNS resolution issue (Node.js `querySrv ECONNREFUSED` against Atlas SRV records on Windows). When re-enabling it, ensure:

- The JWT secret is at least 64 random hex characters
- The MongoDB user has minimum required permissions (not Atlas Admin)
- Network Access is restricted to known IPs, not `0.0.0.0/0` in production

---

## Disclosure Timeline

| Step | Timeline |
|---|---|
| We acknowledge your report | Within 72 hours |
| We confirm and investigate | Within 7 days |
| We develop and test a fix | Within 30 days (critical: 7 days) |
| We release the fix | As soon as tested |
| Public disclosure | After fix is released (coordinated with reporter) |

---

## Hall of Fame

We appreciate responsible disclosures. Reporters of valid vulnerabilities will be credited in the release notes (unless they prefer to remain anonymous).

---

*This security policy was last updated: June 2026*
