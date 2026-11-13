# 🧭 Project Atlas

**[← Home](../README.md)** · [Architecture](HOW_IT_WORKS.md) · [Decisions](DECISIONS.md) · [Roadmap](ROADMAP.md) · [Tests](TEST_PLAN.md)

This is the map of **Ctrl+Alt+Defeat**: what exists, where the code lives, why it exists, and what we haven't proven yet.

## Sectors

| Sector | Code | What happens | Evidence / docs |
|---|---|---|---|
| **01 — Terminal UI** | [`dashboard.py`](../ctrl_alt_defeat/dashboard.py) | Two-pane navigation, ANSI rendering, keyboard input | [Windows checklist](WINDOWS_SMOKE_TEST.md) |
| **02 — Storage** | [`core.py`](../ctrl_alt_defeat/core.py) | Folder sizes, snapshots, SQLite history, file hashes | [Implementation](HOW_IT_WORKS.md) |
| **03 — Job control** | [`jobs.py`](../ctrl_alt_defeat/jobs.py) | Background operations, timestamps, cooperative cancel | [Tests](../tests/test_dashboard_jobs.py) |
| **04 — Cleanup** | [`cleanup.py`](../ctrl_alt_defeat/cleanup.py) | User Temp candidates and approved cleanup | [Safety rationale](DECISIONS.md) |
| **05 — Files / capacity** | [`core.py`](../ctrl_alt_defeat/core.py), [`capacity.py`](../ctrl_alt_defeat/capacity.py) | Verified copy and limited removable-drive probes | [Legacy notes](CAPACITY_TRANSLATOR_ARCADE.md) |
| **06 — Translator** | [`translator.py`](../ctrl_alt_defeat/translator.py) | Command previews; optional Ollama-based suggestions | [AI goals](AI_ASSISTANT_VISION.md) |
| **07 — Optional arcade** | [`arcade.py`](../ctrl_alt_defeat/arcade.py), [`arcade_cli.py`](../ctrl_alt_defeat/arcade_cli.py) | External game adapters, no embedded games | [Installation](ARCADE_SETUP.md) |
| **08 — Versions & health** | [`versions.py`](../ctrl_alt_defeat/versions.py), [`selfcheck.py`](../ctrl_alt_defeat/selfcheck.py) | Recognize older copies and check app contracts | [Test plan](TEST_PLAN.md) |

## Current reality

- **Implemented and headless-tested:** selected Python navigation, job state, scans, limited cleanup, hashing, translator catalog and startup routing.
- **Needs Windows validation:** actual Unicode/ANSI rendering, keyboard behavior, UAC, file-picker usability, Recycle Bin integration, external arcade adapters, local Ollama interaction and packaging.
- **Not implemented:** autonomous AI system maintenance, arbitrary natural-language command execution, bundled arcade binaries, universal OS cleanup, secure-erasure engine.

## How to follow an operation

```text
User input → Terminal UI → Typed operation / preview
         → Background job → Status + timestamped log
         → Verification → Snapshot / result
```

For destructive operations there must also be an explicit **approval and safety policy** stage. A model's suggestion is not authorization to execute.

## References & origins

- [Hiren's BootCD PE](https://www.hirensbootcd.org/) — collection of recovery tools and categorized utilities
- [Easy2Boot](https://easy2boot.xyz/) / [Ventoy](https://www.ventoy.net/) — navigable menus and multi-tool organization
- [Chris Titus Tech WinUtil](https://github.com/ChrisTitusTech/winutil) — inspiration for consolidated Windows workflows, **not bundled**
- [Czkawka](https://github.com/qarmin/czkawka) — future duplicate-file scanning adapter
- [Textual](https://textual.textualize.io/) — a possible future full-screen TUI foundation
- [Ollama](https://ollama.com/) — optional local AI translator backend

The project does not claim ownership or endorsement by these authors. Licenses must be checked before embedding third-party code.

## Evidence trail

[Original script audit](LEGACY_AUDIT.md) · [Bug-review notes](VIDEO_REVIEW_2026-11-13.md) · [How we built it](HOW_IT_WORKS.md) · [Windows smoke tests](WINDOWS_SMOKE_TEST.md)
