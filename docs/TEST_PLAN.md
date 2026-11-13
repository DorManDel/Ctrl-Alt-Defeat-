# v0.5.2 — Pre-push test plan

**Automated local checks:** double-click `RunTests.cmd`. The test suite must show zero failures. A passing Python test is **not** proof that Windows UAC, arcade EXEs, or the Win32 Recycle Bin work.

## Windows regression fixes (2026-11-14)

A real Windows pre-push run exposed three errors that did not occur on Linux:

- **SQLite lock (`WinError 32`)**: `sqlite3.Connection` used as a context manager commits/rolls back but does **not** close the database handle. Snapshot code now explicitly closes connections before Windows removes temporary test folders.
- **Capacity preview + write tests on `C:`**: the system-drive protection was working as designed. The two test fixtures now simulate an external drive **only within the test using a mock**, while retaining the real 5 GiB safety reserve and the write/read/verify/cleanup logic. Production code still refuses capacity tests on the Windows system drive.
- **Guard regression test**: a new test explicitly confirms that a system-drive target is rejected without writing test files.

A successful cross-platform Python test suite is still **not** proof of Windows console/launcher behavior. Rerun `RunTests.cmd` on a Windows machine before merging to `main`.

## On Windows — manual smoke tests

- [ ] Extract into new folder and double-click `START-v0.5.2.vbs`. Verify title says `v0.5.2-dev • by DorManDel`. Close any old app first.
- [ ] Arrow keys, Tab, Esc, F1 and Q work. No frozen screens. Colors and two-pane borders stay aligned after resizing.
- [ ] Storage drive list (`D`), folder browse, and sample-folder scan (`S`) work. Start a large scan, press Esc to browse other modules, observe animated `- / | \\`, timestamp and changing file count. Press `C`; cancellation reaches checkpoint and logs it.
- [ ] Translator → `N`: enter `show free disk space`; see `Get-PSDrive...` without executing it. Try `list Ollama models`, `find large files`, `copy folder` and an unknown request. Unknown request must not produce invented command.
- [ ] Translator → `O`: with Ollama running, enter `check memory usage`; verify the spinner moves, the UI is responsive, and result is marked unverified. Try with Ollama stopped; failure must be visible rather than frozen. Check cancellation behavior.
- [ ] Version Manager → `R`: detects only older sibling extraction directories. It must NOT list the running copy or Git checkout. Test on a **disposable verified old copy only**; enter `RECYCLE` to send it to the Recycle Bin and then restore. Do not test with irreplaceable files or OneDrive data.
- [ ] `PlayArcade.cmd`: open from normal Windows Explorer session. Missing games give clear setup links, not crashes. With vetted official binaries in expected directories, games launch separately and the user can quit them. Launch from Admin should refuse.
- [ ] Self-Test → `R`: run live checks and inspect result logs. Test failing conditions by creating a disposable broken copy, not by altering production files.
- [ ] RunTests.cmd from the source folder: pass, ensure it doesn't write to C:\Windows or launch legacy batch scripts.
- [ ] Confirm user Temp preview and skip changed/locked files. DO NOT test cleanup on important data.
- [ ] Review JSONL logs under `%USERPROFILE%\.ctrl_alt_defeat\logs`. Check timestamps and IDs.

## Release gate

Only push to `dev` after passing automated checks and reviewing source diff. Only open a PR against `main` after real Windows manual smoke tests pass; note unsupported/untested actions clearly in the PR description. Keep screenshots/videos of the resulting Windows terminal.
