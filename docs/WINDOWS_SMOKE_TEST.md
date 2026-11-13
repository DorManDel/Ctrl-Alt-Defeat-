# Ctrl+Alt+Defeat v0.5 — Windows smoke-test checklist

**Run these checks before pushing or creating a pull request.** Never test destructive operations on important data. Tests should use a disposable folder on an ordinary local drive.

## Automated (safe)

Double-click `RunTests.cmd`. Check for the green **PASS** message. It compiles the Python modules and runs unit tests. This is not a Windows UI end-to-end test.

## UI / One-window startup (manual on Windows 11)

- [ ] Double-click `CtrlAltDefeat.vbs` from the extracted folder. One elevated PowerShell window remains visible after UAC; no persistent extra CMD window.
- [ ] Correct banner: `CTRL + ALT + DEFEAT`, not `Ctrl H Defeat`; below it are `v0.5.0-dev` and `by DorManDel`.
- [ ] Left and right panes remain readable at approximately 100×30, 120×40, and after resizing. Purple navigation / cyan content / green-yellow-red job status colors are visible.
- [ ] Tab switches focus; Up/Down and Enter work; Esc backs out of a prompt or returns to left navigation.
- [ ] F1 opens Help. L opens log viewer. Terminal never accumulates old menus vertically.

## Storage / concurrency

- [ ] Open Storage, choose `D` for drive selection and Enter to select a drive. `G` accepts a Unicode folder path. Backspace moves up one folder.
- [ ] Start a scan with `S` on a non-critical test folder. A rotating `- / | \\`, elapsed time, file count, current filename, and progress bar appear. Percent is for **top-level entries**, not bytes.
- [ ] During scan press `Tab`, move through modules and read Event Logs. Scan continues in background.
- [ ] Press `C` or Ctrl+C during a scan. Status moves to CANCELLING then CANCELLED, without crashing. Esc only navigates (does not cancel).
- [ ] Run two complete scans of the same test folder, change a disposable file between them, and compare their snapshots in Snapshot History.
- [ ] Use `Q` during an active scan. Application requests cancellation and exits after a safe checkpoint.

## Safe file operations

- [ ] In File Operations use `N` to choose a disposable small source file and non-existing target; approval requires typing `COPY`.
- [ ] After copying, compare the two files; verify the event logs report completed SHA-256 verification.
- [ ] Repeat with an existing target: operation is rejected; existing target is unchanged.
- [ ] Test cancellation of a sufficiently large disposable copy and confirm that only its incomplete destination is removed; original source remains intact.

## Temp cleanup (optional, use ONLY disposable data)

- [ ] Review `Safe Temp Cleanup` preview; do not type DELETE TEMP unless you understand what will be removed.
- [ ] Verify no symlinks, directories, changed files, or recent files are deleted. Use the unit tests rather than the real user's Temp when possible.

## Logs and error cases

- [ ] See readable timestamps and state changes in Event Logs and `~/.ctrl_alt_defeat/logs/YYYY-MM-DD.jsonl`.
- [ ] Invalid directory entered with `G` produces an error message, not a crash.
- [ ] Check behavior when access to a folder is denied and when terminal is resized.
- [ ] Exit returns cleanly to the original console screen and restores the cursor.

**Do not publish a stable EXE until this list and the automated test workflow pass on Windows.**

## v0.5.2 additions

See [TEST_PLAN.md](TEST_PLAN.md) for the Version Manager, Translator (offline/Ollama), self-test and separate normal-user arcade checks.
