# 🧪 OFFICE-NATOR — Testing Guide

This document covers how to test the voice pipeline, the Excel action library, and the end-to-end system.

---

## Test Architecture

OFFICE-NATOR has three testable layers:

```
Layer 1: Excel Action Library  → verify step sequences (no LLM, no Excel needed)
Layer 2: LLM Intent Pipeline   → verify voice text → correct action_id
Layer 3: Full E2E              → speak → translate → plan → execute → verify
```

---

## Layer 1 — Action Library Verification (Fast, No API Keys)

The `verify_setup.py` script runs 22 critical assertions against the pre-coded action library. Run it any time you modify `excel_actions.py` or `hands/actuator.py`.

```powershell
.\venv\Scripts\python.exe verify_setup.py
```

Expected output:
```
Actions in library : 129
Active provider    : groq

  [PASS] wrap_text: [{'action': 'ribbon', 'keys': ['w']}]
  [PASS] merge_and_center: [{'action': 'ribbon', 'keys': ['m', 'c']}]
  [PASS] autofit_column_width: [{'action': 'ribbon', 'keys': ['o', 'i']}]
  [PASS] set_column_width: [{'action': 'ribbon', 'keys': ['o', 'w']}]
  [PASS] set_row_height: [{'action': 'ribbon', 'keys': ['o', 'h']}]
  [PASS] set_font_size: [{'action': 'ribbon', 'keys': ['f', 's']}]
  [PASS] borders_all: [{'action': 'ribbon', 'keys': ['b', 'a']}]
  [PASS] freeze_top_row: [{'action': 'ribbon', 'keys': ['f', 'r']}]
  [PASS] bold: [{'action': 'hotkey', 'keys': ['ctrl', 'b']}]
  [PASS] toggle_filter: [{'action': 'hotkey', 'keys': ['ctrl', 'shift', 'l']}]
  ... (22 total)

Overall: ALL PASS
```

**All 22 must pass before merging any PR.**

---

## Layer 2 — LLM Intent Classification (Requires Groq/Gemini Key)

The `test_live.py` script sends real text to the LLM and verifies it picks the right `action_id`.

```powershell
.\venv\Scripts\python.exe test_live.py
```

### The 10 Core Test Cases

These represent the most common user commands and the trickiest intents:

| # | User says | Expected action_id | Expected steps |
|---|---|---|---|
| 1 | `"bold karo"` | `bold` | `ctrl+b` |
| 2 | `"font size 16 set karo"` | `set_font_size` | `alt+h, fs, 16, enter` |
| 3 | `"text ko wrap karo"` | `wrap_text` | `alt+h, w` |
| 4 | `"merge karke center karo"` | `merge_and_center` | `alt+h, mc` |
| 5 | `"column ki width autofit karo"` | `autofit_column_width` | `alt+h, oi` |
| 6 | `"row height 30 karo"` | `set_row_height(30)` | `alt+h, oh, 30, enter` |
| 7 | `"Arial font lagao"` | `set_font("Arial")` | `alt+h, ff, Arial, enter` |
| 8 | `"borders sab taraf lagao"` | `borders_all` | `alt+h, ba` |
| 9 | `"pehli row freeze karo"` | `freeze_top_row` | `alt+w, fr` |
| 10 | `"bold aur center dono karo"` | `[bold, align_center]` | `ctrl+b, ctrl+e` |

### Before & After Methodology

The LLM-only approach (before) vs. the library approach (after):

**Before (LLM invents key sequences):**
```
User: "text wrap karo"
LLM response: {"steps": [{"action": "hotkey", "keys": ["alt", "h", "w"]}]}
Result: ❌ FAILS — alt+h+w pressed simultaneously doesn't open ribbon
```

**After (LLM classifies, library executes):**
```
User: "text wrap karo"
LLM response: {"action_id": "wrap_text", "params": {}}
Library lookup: [hotkey(alt,h), wait(0.3), ribbon(w)]
Result: ✅ WORKS — alt+h opens Home tab, then W toggles wrap
```

---

## Layer 3 — End-to-End Tests (Requires Running Full Stack)

### Prerequisites

1. `python server.py` running on port 8000
2. Excel open with a cell selected
3. `frontend` running on port 3000

### Manual Test Script

Open Excel and run these commands via voice (press `Alt+.` before each):

```
Test 1:  "is cell ko bold karo"
         Expected: selected cell becomes bold
         Verify:   Ctrl+B toggles correctly ✓

Test 2:  "font size 18 set karo"  
         Expected: font size changes to 18
         Verify:   Font size box shows 18 ✓

Test 3:  "column ki width autofit karo"
         Expected: column resizes to fit content
         Verify:   Column width adjusts ✓

Test 4:  "text wrap karo"
         Expected: wrap text enabled
         Verify:   Home tab Wrap Text button highlighted ✓

Test 5:  "merge karke center karo"
         Expected: confirmation popup → say "haan" → cells merge
         Verify:   Cells merged, centered ✓ (says "Haan/Nahi" first)

Test 6:  "borders sab taraf lagao"
         Expected: all cell borders applied
         Verify:   Cell shows borders on all sides ✓

Test 7:  "sort A se Z karo"
         Expected: data sorted ascending
         Verify:   Column sorted ✓

Test 8:  "undo karo"
         Expected: last action undone
         Verify:   Ctrl+Z reverses previous action ✓

Test 9:  "pehli row freeze karo"
         Expected: top row frozen
         Verify:   Freeze line appears below row 1 ✓

Test 10: "save karo"
         Expected: workbook saved
         Verify:   Title bar no longer shows unsaved indicator ✓
```

### Verification Popup

After every successful execution, the dashboard shows a green verification banner:

```
┌─────────────────────────────────────────┐
│  ✓  Action completed                    │
│     Toggle bold formatting              │
│     1 step executed · check your Excel  │
│  ████████████░░░░░░░░  auto-dismiss 6s  │
└─────────────────────────────────────────┘
```

This is the "Before/After" check — the popup reminds you to visually confirm the change happened.

---

## Component Smoke Tests

```powershell
# TTS — should speak English and Hindi greeting
.\venv\Scripts\python.exe -m voice.tts_speaker

# Actuator — opens Notepad, types "Hello from Sutra!"  
.\venv\Scripts\python.exe -m hands.actuator

# STT — send a WAV file to Sarvam AI
.\venv\Scripts\python.exe ears\sarvam_stt.py path\to\audio.wav

# Brain — test 5 commands with live LLM (2s delay between each)
.\venv\Scripts\python.exe -m brain.n8n_client

# Gemini API directly
.\venv\Scripts\python.exe test_gemini.py

# Full pipeline (Gemini → parse → return plan)
.\venv\Scripts\python.exe test_pipeline.py
```

---

## Frontend TypeScript Check

```powershell
cd frontend && npx tsc --noEmit
cd "landing page" && npx tsc --noEmit
```

Both must return zero errors before any commit.

---

## Memory System Test

```powershell
.\venv\Scripts\python.exe -m memory.mem0_manager
```

Expected:
```
Current memories: []
After saving preferences: ['User prefers Arial font size 12', ...]
Context for 'make this bold': User preferences and history:
- User often uses bold headers
Context for 'change font': User preferences and history:
- User prefers Arial font size 12
```

Check that `memory/sutra_memory.json` is created and updated.
