# Dynamic console and tab titles

## What changes

The live title is based only on the application version, a known state, and a bounded job name:

- `Ctrl+Alt+Defeat [READY] | v0.5.2-dev`
- `Ctrl+Alt+Defeat [RUNNING] Storage scan | v0.5.2-dev`
- `Ctrl+Alt+Defeat [CANCELLING] Storage scan | v0.5.2-dev`
- `Ctrl+Alt+Defeat [COMPLETED] | v0.5.2-dev`

Windows consoles receive `SetConsoleTitleW`; compatible terminal hosts also receive the standard OSC 0 title sequence. Title changes are emitted only on state transitions, never per animation frame. The previous Windows console title is restored on normal exit. No file path, target, or AI-generated text is included in the tab title.

## Windows Terminal caveat

Windows Terminal can ignore application title updates if `suppressApplicationTitle` is enabled in the profile or tab. Turn it **off** to permit the live tab title. A configured fixed `tabTitle` might also override what the app requests.

Reference: https://learn.microsoft.com/en-us/windows/terminal/tutorials/tab-title

## Test before merging

1. Double-click the normal launcher. Verify the PowerShell window caption shows Ctrl+Alt+Defeat and READY.
2. Start a disposable folder scan. Verify RUNNING + Storage scan appears without flicker and that the UI remains responsive.
3. Cancel a running scan. Verify CANCELLING then CANCELLED (at a safe checkpoint).
4. Exit normally. Verify the previous console title is restored.
5. If running inside Windows Terminal, confirm the tab title changes with `suppressApplicationTitle=false`.
6. Run `RunTests.cmd` and verify the title regression tests pass.

**Status:** feature branch; unit tests for title formatting and a fake Windows API pass. Real Windows console and terminal-tab acceptance is pending.