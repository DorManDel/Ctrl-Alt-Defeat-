# Ctrl+Alt+Defeat — Chat-first UI prototype

**Status: UI design preview only. No Windows operations or AI inference.**

This standalone, dependency-free HTML document demonstrates the next layout before editing the live Python/Windows TUI.

## Try it

Double-click `index.html` in a desktop browser (or open it on a phone). No server, installation, API key or internet connection is needed.

- Type a request in the **chat composer at the bottom of the central panel**, then press Enter. Shift+Enter adds a line.
- Click **Backup Downloads to G:** or another example prompt. The offline demo classifier produces a draft plan; it does not invoke Ollama.
- The right panel shows a distinct plan with **Simple / Detailed / Expert** explanation tabs.
- Click modules in the left navigation to see how the assistant remains global.
- Click **Simulate scan** to inspect a *clearly labeled fake* task progress animation and cancel it. No filesystem access occurs.
- Press **Ctrl+K** for a command palette, **F2** to focus the chat, and **?** to expand the single shortcut footer.
- Use the plan toggle on smaller screens; on phones use the navigation menu button.

## Layout choices to review

1. **Compact branding:** each `CTRL` letter uses a Windows-style color (red, blue, green, yellow). No oversized ASCII logo while doing tasks.
2. **Central chat:** separate YOU/ASSISTANT messages; the persistent composer lives at the bottom of this panel.
3. **Right context panel:** single selected plan; simple, detailed or expert explanation. No duplicated commands inside chat.
4. **Bottom split:** Operation Status and Activity Log are independently readable.
5. **One shortcut footer:** commands appear only at the bottom; clicking `? All shortcuts` reveals more lines.
6. **Staged reveal:** subtle CSS entrance transitions, disabled by `prefers-reduced-motion` or the Reduced Motion command.
7. **Responsive:** three columns on large screens, assistant+sidebar on medium screens, collapsible navigation and plan drawer on mobile.

## Safety boundary

The HTML makes **no network calls, has no file access, does not invoke Ollama, and cannot execute Windows commands**. The demo's recognition is a small rule-based **illustration** of future behavior; it does not measure the actual intent router's accuracy. All job progress is explicitly marked as a simulation. Nothing here is a production approval or execution flow.

## Engineering next steps — not implemented

- Review layout and keyboard feel on the user's screen.
- Port approved layout to Textual (or another tested TUI framework) on a **separate branch**, retaining the existing safe job and policy engines.
- Keep conversation/history UI separate from actual job logs and audit receipts.
- Add model auto-detection, structured response benchmarking, and capability-context resolution.
- Integrate vetted read-only scan previews and a separately tested approval-bound backup adapter.
- Verify Windows PowerShell, Windows Terminal, keyboard-only navigation, resizing, and EXE packaging before merging to `dev`.
