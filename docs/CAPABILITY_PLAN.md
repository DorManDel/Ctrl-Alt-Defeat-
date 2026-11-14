# Ctrl+Alt+Defeat — Capability Plan

**Canonical planning document · 2026-11-14 · Proposal for `feature/intent-control-center`**

[Home](../README.md) · [Atlas](ATLAS.md) · [Roadmap](ROADMAP.md) · [AI approval protocol](AI_ACTION_PROTOCOL.md) · [Machine-readable catalog](../planning/capability_catalog.json)

> **Mission:** One approachable Windows-first control center where people can **inspect → understand → preview → approve → act → verify → recover when possible**. A small optional local AI helps users describe their goal, but never receives a general Administrator shell.
>
> This is a **planning registry**, not an executable tool registry. Being listed here does not make a function available or approved. Statuses must be grounded in code and test evidence.

## Meaning of status, risk and readiness

- **Implemented:** some functionality exists in source and has automated tests; not necessarily polished or validated end-to-end on the user's Windows desktop.
- **Experimental:** prototype / partial integration; may be accessible via CLI, but requires additional verification.
- **Planned:** designed but not integrated as an end-to-end operation.
- **Future:** exploration only (e.g., recovery environment, hardware sanitization).
- **Read-only:** no intended system modification, but may still read private data or impose load.
- **Write:** creates/changes user files. **Destructive:** can remove/replace data. **Privileged:** changes OS configuration/needs elevation. Approval and verification requirements increase with risk.

## Current inventory: what already exists

| Area | Present behavior | Evidence | Status / important limitation |
|---|---|---|---|
| Terminal | Colored two-pane UI, keyboard navigation, status bar/spinner | `ctrl_alt_defeat/dashboard.py`; tests | Implemented; Windows UI smoke testing separate |
| Storage | Browse drives/folders, recursive scan, snapshot history and comparison | `core.py`, `jobs.py` | Implemented; logical file sizes are not guaranteed unique on-disk allocation |
| Visual storage | Toggle simple sized bars after scan | `dashboard.py` | Experimental, **not** a WizTree treemap |
| File copy | Explicit single-file copy without overwrite, SHA-256 verification, cancellation | `jobs.py`, `core.py` | Implemented; recursive backup/restore not yet present |
| Cleanup | Preview and approved deletion of scoped, eligible user Temp files | `cleanup.py` | Implemented in narrow scope; **not** blanket OS cleanup |
| Capacity | Bounded write/read verification with own-file cleanup | `capacity.py` | CLI only; refuses Windows system drive; **not** secure wipe |
| Diagnostics | Limited read-only System Doctor | `dashboard.py`, `__main__.py` | Experimental; not a system repair engine |
| Task operations | One active job, timestamps, cooperative cancellation, JSONL audit | `jobs.py` | Implemented; **not** multi-job queue or crash-safe resume |
| Navigation / activity | Back-stack and operator activity journal | `navigation.py`, `activity.py` | Experimental; **Back is not Undo** |
| Version control | Recognizes older sibling copies, refuses active and Git source folders | `versions.py` | Experimental; Recycle Bin Windows acceptance pending |
| Translator | Offline curated recipes; local Ollama command suggestions | `translator.py` | Preview only; output never automatically executed |
| Intent Lab | Local Ollama structured intent with allowlisted `scan_storage`, `backup_files`, etc. | `intent_router.py`, tests | Experimental; no execution adapter is connected |
| Arcade | Launcher for separately installed external games | `arcade.py` | Partial; games not bundled or guaranteed installed |
| Validation | Python tests, Windows CI/build, manual smoke checklist | `tests/`, `.github/workflows/` | Automated checks are not a substitute for manual acceptance |

## Full functional catalog and priorities

These are user-facing capabilities. Detailed machine-readable entries, risks, providers and prerequisite parameters live in [`planning/capability_catalog.json`](../planning/capability_catalog.json). **P0** foundation, **P1** next useful feature, **P2** expansion, **P3** longer term. Progress is tracked in the Roadmap.

### A. Overview, Storage & Cleanup

| ID | User action | Status | Next milestone / reason |
|---|---|---|---|
| `storage.browse` | Browse drives/folders | Implemented | Favorites, breadcrumbs, search and sorting |
| `storage.scan` | Scan folder sizes; record snapshot | Implemented | Allocate-vs-logical accuracy and exclusions |
| `storage.compare` | Compare before/after space | Implemented | Explain actual recovered vs merely predicted |
| `storage.bars` | Show simple storage size bars | Experimental | Keyboard filters and drill-down |
| `storage.treemap` | Interactive WizTree-like view | Planned P2 | Use verified scan/import data, never fabricated measurements |
| `storage.wiztree_import` | Import WizTree CSV | Planned P1 | Handle hard links/allocated values explicitly |
| `storage.large_files` | Locate large files by type/age | Planned P1 | Exclusions, symlink protection and cancellable scans |
| `cleanup.temp_preview` | Identify eligible old Temp items | Implemented | Visibility, excludes active and protected items |
| `cleanup.temp_delete` | Delete scoped eligible user Temp | Implemented | Exact targets, fresh revalidation, audit |
| `cleanup.windows_components` | Analyze Windows Update/component cleanup | Planned P1 | Prefer DISM/OS APIs, not arbitrary cache-folder wipes |
| `cleanup.logs` | Inspect and clean opted-in application logs | Planned P2 | Never recursive drive-root `*.log` deletion |
| `cleanup.duplicates` | Group duplicates; suggest retention | Planned P1 | Czkawka JSON results, **never auto-delete** |

### B. Files, Backup & Conversion

| ID | User action | Status | Next milestone / reason |
|---|---|---|---|
| `files.copy_verified` | Copy one file and SHA-256 verify | Implemented | Transfer queue and consistent audit |
| `files.hash` | Calculate content hash | Implemented (internal) | Standalone user-facing command |
| `files.backup_folder` | Recursive folder backup | Planned P0 | Dry-run, safe overwrite policy, verify, restore tests |
| `files.restore` | Restore a verified backup | Planned P1 | Compare versions and conflict handling |
| `files.quarantine` | Recoverably remove user-selected files | Planned P1 | Owned quarantine, retention and restore |
| `files.archive` | Create/list/extract archives | Planned P2 | 7-Zip adapter, path traversal protection |
| `files.media_convert` | Convert video/audio/subtitles | Planned P2 | FFmpeg + ffprobe, preview and quality options |
| `files.image_convert` | Convert/compress/resize images | Planned P2 | ImageMagick, preserve original by default |

### C. Processes, Apps, Development & Device Maintenance

| ID | User action | Status | Next milestone / reason |
|---|---|---|---|
| `system.doctor` | Basic system diagnostics | Experimental | Actionable results, privacy-aware reports |
| `process.tree` | View running apps, CPU/RAM trends | Planned P1 | psutil/Windows counters; no auto-termination |
| `process.handles` | Explain files locked by processes | Planned P2 | Launch Process Explorer/approved diagnostics |
| `process.events` | Capture scoped file/process/registry events | Planned P2 | Procmon manual capture with bounded retention |
| `software.inventory` | Show installed apps/versions | Planned P1 | WinGet inventory; explain managed/unmanaged apps |
| `software.install` | Install/update selected app | Planned P2 | WinGet with exact package ID, source and confirmation |
| `software.uninstall` | Uninstall selected app | Planned P2 | Vendor/WinGet uninstall, potential data-loss warning |
| `system.servicing` | Inspect/repair Windows components | Planned P1/P2 | Read-only analyze first; DISM/SFC writes require elevation |
| `dev.steam` | Inspect Steam caches/update staging | Planned P1 | Never silently modify installed/active games |
| `dev.unity` | Inspect Unity editors/project versions/caches | Planned P1 | Preserve referenced versions and projects |
| `dev.ollama` | List and manage model storage | Planned P1 | `ollama list`, protected models, controlled removals |
| `device.capacity_probe` | Bounded external-drive write/verify | Implemented (CLI) | Verify recoverability and real-drive acceptance |
| `device.smart_health` | Read SMART/disk health | Planned P2 | smartmontools/OS APIs, read-only by default |
| `recovery.boot_environment` | Learn/create vetted external recovery media | Future P3 | Ventoy/Easy2Boot/Hiren/MediCat/Strelec: not runtime libraries |
| `device.secure_erase` | Secure sanitization | Future P3 | Separate hardware-specific flow; no false claims about zeros |

### D. AI, History & Operation Control

| ID | User action | Status | Next milestone / reason |
|---|---|---|---|
| `ai.offline_suggest` | Curated command help | Implemented | Simple/detailed recipe explainer |
| `ai.ollama_command_preview` | Local suggested command text | Experimental | Explicitly **untrusted and not executable** |
| `ai.classify_intent` | Turn Hebrew/English request into typed plan | Experimental | Benchmark latency, intent quality and missing-field recovery |
| `ai.explain_command` | Explain every audited parameter/flag | Planned P0 | Two accessible explanation levels; supported recipe catalog |
| `ai.approved_dispatch` | Run a validated tool after user approval | Planned P0 | Independent executor, no shell interpolation |
| `history.navigation` | Back/forward screen-state stack | Experimental | Preserve cursor/filter; no side-effect reversal |
| `history.activity` | Browse local operator activity journal | Experimental | Privacy controls and export/redaction |
| `history.job_audit` | View timestamped jobs/results | Implemented | Per-step receipts and measured outcomes |
| `history.version_manager` | Inspect older installations for optional recycle | Experimental | Safety test with OneDrive and Git checkouts |
| `history.self_test` | Launch local checks and view outcomes | Implemented | Windows CI plus real end-to-end tests |

## What happens to users' requests?

1. **Discover:** user asks in Hebrew/English; the assistant classifies against a **finite capability ID list**. When unsupported, it says so or asks for the one missing parameter.
2. **Plan:** typed arguments (source, destination, paths, exclusions), intended effect, selected adapter and risk. Do not invent paths or claim work occurred.
3. **Explain:** display one-sentence plain-language meaning and expandable flag-by-flag meaning. The UI should distinguish the adapter's vetted preview command from an untrusted AI-generated suggestion.
4. **Inspect:** show exact targets and applicable dry run; scanning a folder or invoking a diagnostic is also an operation requiring user permission if initiated by AI.
5. **Approve:** a user action authorizes **only this exact validated plan**, not arbitrary shell privileges. Any change invalidates approval. Higher-risk actions require a stronger confirmation.
6. **Execute:** a separately permissioned executor calls a registered adapter with typed arguments, a safe timeout, bounded output and no `shell=True` or `Invoke-Expression`.
7. **Verify + log:** record the operation ID, preview/approval hash, before/after measurements, completion state, errors and an *actually supported* undo path.

See the [AI Action / Explanation / Approval Protocol](AI_ACTION_PROTOCOL.md) for an end-user example and testable design contract.

## Exclusions and non-goals

- No general AI Administrator shell, model-authored PowerShell execution, auto-approved deletion or arbitrary remote scripts.
- No indiscriminate Windows logs, driver cache, Prefetch or `SoftwareDistribution` deletion.
- No unauthorized password extraction, license bypass or cracking in the default product. Authorized recovery and owned-license inventory can be reviewed separately later through vendor-supported workflows.
- No false claim that filling a drive with zeros and deleting the files securely erases an SSD or establishes the advertised full capacity.
- Never redistribute third-party executables, ISOs or proprietary assets before checking license, provenance and update strategy.

## Acceptance criteria for every capability

- [ ] Clear input schema and preconditions; rejects unknown/untrusted paths and unsafe junctions/symlinks.
- [ ] Simple and detailed explanation, plus actual proposed effect and limitations.
- [ ] Non-destructive preview (if supported), accurate risk category, no hidden actions.
- [ ] Explicit operation-scoped approval where needed; independent confirmation for destructive effects.
- [ ] Running, waiting, cancelling, complete and failed states; safe checkpoints with timestamped logs.
- [ ] Integration tests with disposable fixtures; no admin rights for ordinary tests.
- [ ] Result verification and real measurement vs estimate; documented Undo policy.
- [ ] Windows CI **and** real Windows smoke test before merging into `main`.

## Source references / next links

- [Microsoft WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
- [Robocopy options](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy/)
- [Czkawka CLI and JSON export](https://github.com/qarmin/czkawka/blob/master/instructions/Instruction_CLI.md)
- [WizTree CSV documentation](https://diskanalyzer.com/guide)
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
- [External tool assessment](ADAPTER_EVALUATION.md)
