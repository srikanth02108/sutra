# 🤝 Contributing to OFFICE-NATOR

Thank you for considering contributing to OFFICE-NATOR! This project is built for Bharat — every improvement helps millions of regional language speakers work more productively.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Environment Setup](#environment-setup)
- [Project Areas](#project-areas)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold these standards.

---

## 🐛 Reporting Bugs

1. **Search existing issues** first — it may already be reported
2. **Open a new issue** with the label `bug`
3. Include:
   - OS version and Python/Node versions
   - Steps to reproduce (exact voice commands if relevant)
   - What you expected vs what happened
   - Terminal output / error messages
   - Which LLM provider you were using

**For security vulnerabilities:** See [SECURITY.md](SECURITY.md) — do **not** open a public issue.

---

## 💡 Requesting Features

1. Open an issue with the label `enhancement`
2. Describe:
   - The use case ("I want to say X and have Y happen")
   - Which language/dialect this helps
   - Whether it's a new Excel action, new voice feature, or UI improvement

**Good feature ideas:**
- New Excel actions not yet in `excel_actions.py`
- Support for additional Indian languages
- Additional office app support (Word, PowerPoint, Google Sheets)
- Improvements to the VAD silence detection
- Memory system enhancements

---

## 🔀 Pull Request Process

### 1. Fork and clone

```bash
git clone https://github.com/YOUR_USERNAME/sutra.git
cd sutra
git checkout -b feature/your-feature-name
```

### 2. Set up the environment

Follow [SETUP_GUIDE.md](SETUP_GUIDE.md) completely. PRs from broken environments won't be reviewed.

### 3. Make your changes

- Keep commits atomic and descriptive
- One feature/fix per PR
- Update `EXCEL_ACTIONS.md` if you add new actions to `excel_actions.py`
- Update `.env.example` if you add new env vars

### 4. Test your changes

```powershell
# Verify all 129 actions still produce correct step sequences
.\venv\Scripts\python.exe verify_setup.py

# TypeScript check for frontend
cd frontend && npx tsc --noEmit
cd "landing page" && npx tsc --noEmit
```

### 5. Self-review with OFFICE-NATOR

> 🤖 **Before submitting your PR, use OFFICE-NATOR to test your changes.** If you're modifying Excel actions, open Excel and voice-test the modified commands. This is the best way to verify real-world behavior.

### 6. Open the PR

- Title: `feat:`, `fix:`, `docs:`, `refactor:`, or `chore:` prefix
- Description: what changed and why
- Link any related issues

---

## 📐 Coding Standards

### Python (backend)

- Follow PEP 8
- Type hints on all public functions
- Docstrings on all classes and public methods
- Use `logger = logging.getLogger(__name__)` — no `print()` in production code
- Actions in `excel_actions.py` must return `List[dict]` and use only `_hotkey()`, `_ribbon()`, `_key()`, `_type()`, `_wait()` helpers

### TypeScript (frontend)

- Strict TypeScript — no `any` without explicit justification
- Framer Motion for all animations
- No inline styles unless using CSS variables
- Component props must have explicit types
- `useCallback`/`useMemo` for all handler functions passed as props

### Adding Excel Actions

When adding new actions to `excel_actions.py`:

```python
# 1. Write the function
def your_action(param: type = default, **kw) -> list:
    """One-line description."""
    return [
        *_home_tab(),   # opens the right ribbon tab
        _ribbon("x", "y"),  # ribbon key sequence
    ]

# 2. Add to REGISTRY
"your_action": {
    "fn": your_action,
    "desc": "What it does",
    "confirm": False,   # True if destructive
    "params": ["param"],
},
```

Then verify:
```python
from excel_actions import get_steps
steps = get_steps("your_action", param=value)
assert len(steps) > 0
```

---

## 🌍 Adding Language Support

OFFICE-NATOR uses Sarvam AI's `translate` mode which converts Hindi/Marathi directly to English. To extend support:

1. Check if Sarvam AI supports the target language at [docs.sarvam.ai](https://docs.sarvam.ai)
2. Add language-specific example commands to `EXCEL_ACTIONS.md`
3. Test the STT pipeline with audio samples

---

## 🗂️ Project Areas

| Area | Files | Skills needed |
|---|---|---|
| New Excel actions | `excel_actions.py`, `EXCEL_ACTIONS.md` | Python, Excel knowledge |
| LLM prompt tuning | `brain/n8n_client.py` | Prompt engineering |
| Voice pipeline | `ears/vad_listener.py`, `ears/sarvam_stt.py` | Python, audio |
| Frontend UI | `frontend/components/` | React, TypeScript, Framer Motion |
| Landing page | `landing page/components/` | React, TypeScript |
| Memory system | `memory/mem0_manager.py` | Python |
| Documentation | `*.md` files | Technical writing |

---

## Questions?

Open a GitHub Discussion or file an issue with the `question` label.
