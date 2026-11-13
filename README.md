# Ctrl+Alt+Defeat 🛠️

> **When Windows fights back, press harder.**

**Ctrl+Alt+Defeat** (`CtrlAltDefeat`) is a Windows-first, terminal-based toolkit for storage diagnostics, safe file operations and developer utilities. Built for people who want to understand what a system tool will do *before* it does it.

**Status:** v0.3 alpha — source-based Python application. Not yet a standalone executable, and not yet tested on a physical Windows installation.

## Quick start — Windows

1. Extract this repository to a folder.
2. Ensure Python 3.10+ is installed and available through `py` or `python`.
3. **Double-click `CtrlAltDefeat.cmd`** and approve the Windows UAC elevation request.
4. Choose a module in the terminal menu.

No typed startup command is needed. The menu works without optional packages; `rich` enables colored tables (`py -m pip install -r requirements.txt`). If you prefer a PowerShell launcher, `start.ps1` also runs the menu but doesn't elevate automatically. `launcher.ps1` performs elevation when called by `CtrlAltDefeat.cmd`.

## Modules available now

| Module | Behavior |
|---|---|
| Storage snapshots | Read-only directory scans with local SQLite history |
| Snapshot comparison | Compare scanned directory sizes and free space |
| Temp preview | Read-only inspection, no deletion |
| Copy / backup | Single-file copies, explicit confirmation, SHA-256 verification |
| Capacity test | Limited write/read test on non-system drives; verifies its own files |
| Command translator | Vetted command suggestions only, does not execute generated commands |
| Arcade | Curated links, not bundled games |
| System doctor | Read-only local path checks |

## Optional command-line usage

```powershell
py -m ctrl_alt_defeat menu
py -m ctrl_alt_defeat scan "C:\Program Files (x86)\Steam\steamapps" --save
py -m ctrl_alt_defeat history
py -m ctrl_alt_defeat compare 1 2
py -m ctrl_alt_defeat doctor
```

## Safety boundaries

- Original `.bat` scripts are preserved **verbatim** in `legacy/` and never executed by this project.
- No automatic service changes, Windows Update cache removal, registry editing, or disk wiping.
- The capacity test is **not** a secure erase or full drive authentication tool.
- Copy and backup currently support single files, without overwriting existing targets.
- Elevation is requested at launch for the intended admin workflow; a future release should use per-operation privileges so games and browsing do not run elevated.
- The snapshot database remains in `~/.winforge/snapshots.sqlite3` for compatibility with previous WinForge builds. Likewise, existing `.winforge-capacity-*` test directories keep their names so recovery tools still recognize them.

## Project structure

```text
CtrlAltDefeat/
├── CtrlAltDefeat.cmd     # Double-click launcher
├── launcher.ps1          # UAC elevation and Python invocation
├── start.ps1             # Manual PowerShell entry point
├── ctrl_alt_defeat/      # Python CLI, storage, capacity, translator
├── tests/                # Automated tests
├── docs/                 # Module notes, roadmap and legacy audit
└── legacy/               # Historical scripts — never executed
```

## Development

```powershell
py -m unittest discover -s tests -v
```

Planned: interactive animated TUI, recursive verified backups, cleanup quarantine/rollback, opt-in tool adapters (WizTree, WinUtil, Czkawka, FFmpeg), and portable `.exe` builds.

## Licensing and attribution

The legacy batch files are retained as user-contributed historical examples. Third-party games and system utilities are **not bundled**. Review each dependency's license before vendoring or redistribution. **Choose a repository license before publishing**; a LICENSE file has intentionally not been assumed.

## Branding

- **Display name:** Ctrl+Alt+Defeat
- **Repository slug:** `CtrlAltDefeat`
- **Windows entry point:** `CtrlAltDefeat.cmd`
- **Python package:** `ctrl_alt_defeat`
- **Future executable:** `CtrlAltDefeat.exe`
- **Tagline:** *When Windows fights back, press harder.*

Not affiliated with Microsoft. No guarantees of recovered disk space or suitability for critical system repairs.
