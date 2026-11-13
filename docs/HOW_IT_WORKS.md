# How we built Ctrl+Alt+Defeat (v0.5.2)

## 1. Timeline and design lessons

The project began as eight Windows batch scripts written years earlier to clean Temp, logs, Windows Update caches and Prefetch. Those scripts provided **real disk-space savings**, but some used broad recursive deletion or Windows service changes. They are archived unmodified under `legacy/` for historical attribution and not run by the current app.

- **v0.1–v0.3**: Python CLI (`argparse`), SQLite snapshot history, copy/backup, capacity probe, rule-based translator, external arcade links. Initially the terminal printed Rich formatting tags when Rich was not installed.
- **v0.4**: custom terminal menu, ASCII and arrow navigation; menu would freeze during long scans. The title glyphs were wrong and some screens were placeholders.
- **v0.5.0**: added two-pane dashboard and worker jobs but **the launcher still routed to the old UI**. Unit tests missed the actual entry point.
- **v0.5.1**: corrected startup routing, tested `__main__ -> dashboard.run`, added status + author + logs. User tested the real UI on Windows.
- **v0.5.2**: implemented more useful command matching and optional Ollama preview, an external arcade adapter with standard-user launcher, old-version detection/recycle, self-check and expanded test coverage.

## 2. Architecture

```text
CtrlAltDefeat.cmd or START-v0.5.2.vbs
    -> launcher.ps1 (Windows UAC and Python discovery)
        -> python -m ctrl_alt_defeat menu
            -> __main__.run() -> dashboard.run()
                -> Controller (keyboard state, navigation)
                    -> JobManager (worker thread, cancel event, timestamps)
                        -> core.py (scan/snapshots/copy)
                        -> cleanup.py (scoped user Temp)
                        -> translator.py (offline recipes + optional Ollama HTTP)
                        -> versions.py (sibling version discovery, recycle)
                        -> selfcheck.py (non-destructive health checks)
                -> dashboard.render() (color + ASCII, two panes, status)
PlayArcade.cmd (normal-user) -> arcade_cli.py -> arcade.py -> user-installed game
```

### Startup behavior

`CtrlAltDefeat.cmd` calls PowerShell and `launcher.ps1`, which may open a second elevated process via UAC. `START-v0.5.2.vbs` avoids a persistent first console but does not eliminate UAC's separate process. Future single-exe packaging will simplify this. The Python module dispatcher is a **required regression test**, because we shipped a wrong route once.

### User interface

`dashboard.py` uses ANSI terminal escape sequences to draw full-screen frames; Windows VT mode is enabled through the console API. It currently uses no third-party UI library. ASCII letters are defined explicitly to avoid accidental misspelling of the logo. Palette: purple for navigation, cyan for details, yellow for version/warnings, green for good states, red for failures. Frame redraw ~150ms while active. Hotkeys are sent to Controller via a platform-specific input reader. This is a custom TUI, not Textual.

### Job lifecycle and logging

`JobManager` runs one worker at a time in a daemon thread and tracks queued/running/cancelling/completed/failed. Every event is saved as JSONL at `%USERPROFILE%\.ctrl_alt_defeat\logs\YYYY-MM-DD.jsonl`. The worker calls `checkpoint()` to report files/bytes and check cancellation. `Esc` leaves a screen; `C` requests cancellation. Cancelling is **cooperative**: a blocked OS call may not abort instantly. Known-count operations show a percent. Unknown-total tasks show spinner/elapsed/file count, not a made-up percentage.

### Storage engine

`core.scan` enumerates immediate children, recursively totals logical file bytes, skips symlinks/junctions and logs access errors. SQLite snapshots live at `%USERPROFILE%\.winforge\snapshots.sqlite3` for old data compatibility. Numbers represent logical sizes, **not necessarily uniquely allocated disk bytes**. Snapshots compare entries of the same root only.

### Safe operations

- Copy: source file -> new exclusive destination (`xb`) -> SHA-256 verify. No overwrite. Cancellation removes only its own incomplete target.
- Temp: only explicitly previewed regular files directly in the current user's Temp directory, after age/identity revalidation, explicit confirmation. Does not recursively delete system logs/Prefetch or servicing data.
- Versions: checks package markers and numeric version, refuses current folder, Git checkouts, links/junctions, unexpected paths; Windows Recycle Bin after `RECYCLE` confirmation. Any OneDrive-synced folder deletion may propagate to the cloud.
- Translator: offline trusted recipes; optional local Ollama generates **unverified text preview**. No `Invoke-Expression`, `shell=True` or automatic command execution.
- Arcade: separate standard-user launcher for separately installed MIT/GPL terminal games; neither game is included.

## 3. Why this structure is useful

UI, job orchestration, system adapters and data operations are separate. That makes it possible to add Linux/macOS backends in future without rewriting the whole interface. Windows-only features (UAC, Shell Recycle Bin) live in adapter-like modules and are tested with injected mocks on non-Windows platforms.

## 4. Known limitations

- The full GUI is not embedded; full-screen TUI depends on terminal width and ANSI compatibility.
- True byte/volume scan progress is hard without an upfront inventory; percent counts completed top-level entries.
- Windows-specific UAC, Recycle Bin, game EXE behavior still require real-device tests.
- Version management only checks **sibling extracted folders**, not the whole PC or arbitrary ZIPs.
- The game executables aren't shipped. One-click arcade helper needs an authorized game binary.
- Ollama HTTP translation requires localhost Ollama, and a suitable model; AI responses must be reviewed.

## 5. Development workflow

Always test a new version in a **separate extracted directory** from the Git checkout. Run `RunTests.cmd`, then follow `docs/TEST_PLAN.md`. Use `dev` branch for source changes and PR to `main` after Windows smoke tests. Don't publish packaged binaries that have not been smoke-tested on Windows.
