# Activity history & navigation

[← Atlas](ATLAS.md) · [Control Center](CONTROL_CENTER.md)

The current build maintains two complementary, local audit channels:

- **Task log:** `~/.ctrl_alt_defeat/logs/YYYY-MM-DD.jsonl` (existing `JobManager`) stores queued, started, cancelled, completed and failed tasks with timestamps and job IDs.
- **Operator activity:** `~/.ctrl_alt_defeat/activity.jsonl` (new `ActivityJournal`) stores module navigation and plans proposed by offline rules or Ollama. It does **not** store raw prompts, model text or file paths in this journal by default; it always records `executed: false`. These events are visible within Event Logs.

**Navigation history** uses a bounded 64-entry LIFO stack for screen, focus, directory, drive-selector mode and selection. `Esc` returns to a saved state; active jobs continue. This history is in-memory only and is not a file-operation undo mechanism.

Only real adapters may report actual execution, and only after verifying an operation result. Future durable operation transactions will record source/target, approval, before/after disk snapshots, cleanup eligibility, hashes and specific recovery capability. Store detailed paths locally with explicit access controls; never send these event logs to a model or remote service without permission.

**Known limits:** no universal file undo, no multi-job queue yet, no crash-safe resume, and no system-wide activity monitoring. Windows console/real local Ollama acceptance is still pending.
