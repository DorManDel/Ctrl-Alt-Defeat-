# External Tool / Adapter Evaluation

[← Capability Plan](CAPABILITY_PLAN.md) · [Atlas](ATLAS.md) · [AI Protocol](AI_ACTION_PROTOCOL.md)

**Status: research & design, not proof that a tool is installed, bundled or callable from Ctrl+Alt+Defeat.** Every adapter requires version detection, source/license review, typed options, stdout/stderr/exit-code handling, timeouts, cancellation, no-shell spawning, path validation, privacy handling and offline/absent-tool fallback.

| Tool | What it provides | Feasible integration | Priority / constraint |
|---|---|---|---|
| **Microsoft WinGet** | Inventory, install, upgrade, uninstall, app export/import | **Strong CLI adapter**: typed package IDs; parse supported output, log known exit codes | P1 inventory, P2 changes. Avoid broad package selectors |
| **Robocopy** (built into Windows) | Robust recursive copying, restart/retry options, logs, list-only mode | **Strong native adapter**: structured copy plan, `/L` preview, controlled actual run, verify | P0 backup. Avoid accidental `/MIR` purge; interpret Robocopy return codes correctly |
| **WizTree** | Fast NTFS space analyzer, logical vs allocated, treemap | **Import/launch adapter**: import officially supported CSV (incl. `Allocated`) or launch user-installed app | P1. Check license/CLI terms; don't silently bundle; beware hard-link double counting |
| **Czkawka / Krokiet** | Duplicate files, similar pictures/videos, invalid links, big/empty/temp files | **Strong CLI adapter**: user-installed `czkawka_cli`, JSON output for structured review | P1 scan; removal stays in our own approval workflow. No automatic duplicate deletion |
| **Sysinternals Process Explorer** | Process tree, open handles/DLLs, identify locking process | **Launch/context adapter** first; deep integration later only with supported APIs | P2. UI-oriented; do not invent machine-readable export interface |
| **Sysinternals Process Monitor** | Time-scoped file/registry/process events, filters and capture logs | **Controlled external capture adapter** or explicit launch, import verified export | P2. Trace can be sensitive, large and costly; never capture indefinitely by default |
| **CTT WinUtil** | Windows apps, tweaks, fixes, updates, queued actions, presets | **Reference + opt-in launch**; implement our *own* typed Windows actions using documented OS APIs before considering deep integration | P2. Avoid automatic downloading and executing a network PowerShell script or unattended Admin presets |
| **DISM / SFC / Windows APIs** | Windows component-store analysis/repair, system diagnostics | **Native controlled adapter**, read-only analysis first, privileged repair separately | P1/P2. Reboots/permissions and rollback boundaries must be explicit |
| **FFmpeg / ffprobe** | Audio/video conversion, probing streams/codecs | **Strong CLI adapter** with exact paths and trusted option templates | P2. Respect format safety, license and processor cost; output new file by default |
| **ImageMagick** | Resize, convert, optimize image batches | **Strong CLI adapter** with safe input/output and capped resources | P2. Do not use in-place batch overwrite as default |
| **7-Zip** | Archive create/list/test/extract | **Strong CLI adapter** after licensed distribution review | P2. Prevent archive path traversal, encrypted archive surprises and overwrites |
| **smartmontools** | SMART device health and attributes | **CLI/diagnostic adapter** | P2. Hardware/controller support varies; not a health guarantee |
| **Ollama** | Local model inventory and JSON-schema structured classification | **Local HTTP adapter**, localhost only and no model tool execution | P0 intent lab / P1 model manager; benchmark smaller models before promoting |
| **Textual** | Directory trees, data tables, graphs and keyboard/mouse TUI | **UI library**, not a system-operation adapter | P2 future interface framework; keep operation engine independent |
| **Steam / Unity / Ollama native app state** | Game install/update staging, Unity editor/project versions, local model storage | **App-specific discovery adapters**; use supported metadata/APIs only | P1. No unreviewed edits of manifests or running apps |
| **MediCat USB / Hiren's BootCD PE / Sergei Strelec** | Separate boot/recovery environments with many bundled utilities | **Reference, external boot guidance and optional launch only**; *not* typical in-process adapters | P3. Mixed third-party licensing/distribution, disk/boot safety, separate recovery environment |
| **Ventoy / Easy2Boot** | Multi-boot USB organization | **Boot-media workflow inspiration**; separate opt-in device writer, not normal CLI module | P3. Writing a boot USB can destroy prior drive contents; double-check physical target |

## Integration decision ladder

1. **Link only** — show provenance/docs and detect installed version; no execution.
2. **Read-only adapter** — structured invocation or import, machine-readable results, no changes.
3. **Previewable write adapter** — typed operation, supported dry run, exact destination, approval, result verification.
4. **Privileged adapter** — separate elevated broker, explicit UAC, narrow OS API operations; never allow an AI shell.
5. **Recovery/boot integration** — standalone project with media, licensing and physical-drive verification.

## Adapter contract (proposed)

- `adapter_id`, `version`, `supported_platforms`, `detected_binary/source`, `license_link`
- `capabilities[]` with input JSON schema, permission level, dry-run support, cancellation and undo support
- `build_preview(args)` returns human-friendly summary and **vetted tool-owned command specification**; does not execute
- `run(approved_plan)` accepts only the signed, unchanged operation plan and returns structured events/verification
- No shell string interpolation; external calls should use argument arrays, fixed executable paths and explicit working directories
- Logs must distinguish observed facts from estimated results and redact private paths/contents when exported

## Trial sequence

1. Build **Robocopy** preview + verified recursive backup against disposable folders.
2. Build **Czkawka** JSON duplicate scan (read-only) and **WizTree** CSV import.
3. Build **WinGet** inventory and optionally an install preview.
4. Build FFmpeg/ImageMagick conversions with no overwrite and cancel checkpoints.
5. Add Process Explorer/Procmon launch and Windows event import; add WinUtil informational link rather than auto-running its scripts.
6. Put recovery/boot tools in a completely separate Devices & Recovery phase.

## Primary docs

- [CTT WinUtil](https://github.com/ChrisTitusTech/winutil) and [WinUtil guide](https://winutil.christitus.com/guides/getting-started/)
- [WizTree](https://diskanalyzer.com/guide) and [Czkawka CLI](https://github.com/qarmin/czkawka/blob/master/instructions/Instruction_CLI.md)
- [Robocopy](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy/) and [WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
- [Process Monitor](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon) and [Process Explorer](https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer)
- [FFmpeg](https://ffmpeg.org/ffmpeg.html), [ImageMagick](https://imagemagick.org/script/command-line-processing.php)
- [MediCat tools](https://docs.medicat.dev/usb/tools/), [Hiren](https://www.hirensbootcd.org/), [Sergei Strelec](https://sergeistrelec.name/), [Ventoy](https://www.ventoy.net/), [Easy2Boot](https://easy2boot.xyz/)
