# Explain → Preview → Approve → Execute: AI Action Protocol

[← Capability Plan](CAPABILITY_PLAN.md) · [Adapter Evaluation](ADAPTER_EVALUATION.md) · [Control Center](CONTROL_CENTER.md)

**Status: design contract; NOT an implemented AI executor.** The existing Ollama Intent Lab generates validated plans **only**. The current, older Translator may display untrusted PowerShell suggestions; none may be executed automatically.

## The fundamental rule

**Understanding a request is not permission to act.** The assistant may classify and explain a request. It cannot run commands, start background scans on the user's behalf, download executables, install packages, delete logs, change Windows services or approve its own proposal without an affirmative user action authorizing the exact operation.

## Required state machine

```
REQUESTED → INTERPRETED → VALIDATED → EXPLAINED → PREVIEW_READY
                        ↘ NEEDS_INPUT / BLOCKED
PREVIEW_READY → USER_APPROVED → REVALIDATED → RUNNING → VERIFIED
                                       ↘ CANCELLED / FAILED / PARTIAL
```

- `INTERPRETED`: allowlisted capability + typed arguments + model identity and confidence. Confidence is **not** authorization.
- `VALIDATED`: normalize paths without accepting wildcards for deletion; reject unsupported roots, changed targets, junction/symlink escapes, self-modification and protected project locations. Insist on exact destinations.
- `EXPLAINED`: one-line summary + expandable flag/parameter breakdown, effects, risk, privilege, expected outputs, cancellation and undo policy; explain what is **not** done.
- `PREVIEW_READY`: plan is non-executable until user approves. A preview that reads filesystem content itself needs an explicit `Preview / Scan` action from the user.
- `USER_APPROVED`: bind approval to canonical plan ID, input arguments, adapter/version, target fingerprints and expiry; if anything changes, approval is invalid.
- `REVALIDATED`: stat/check actual paths immediately before dispatch; restrict privileges to the operation.
- `RUNNING`: trusted adapter executes **only predefined typed behavior**; no arbitrary model-authored shell text. JobManager tracks state, progress and cancellation checkpoints.
- `VERIFIED`: compare expected vs actual results (bytes, counts, hashes, exit status); write immutable-by-application event/receipt. Offer Undo only if supported and tested.

## Example: simple and detailed explanations

User: **"Back up my project folder from C:\Example\Project to D:\Backups\Project"**

Simple explanation (default):

> Copy all files and subfolders from the chosen project into a separate backup location on D:. Keep the originals. Preview the file list before copying. The backup may need free space and will not delete any source file.

A **trusted Robocopy adapter** could produce the following *illustrative dry-run command*:

```powershell
robocopy "C:\Example\Project" "D:\Backups\Project" /E /L /R:1 /W:1
```

Detailed explanation (expandable):

| Segment | What it means | Why it is here |
|---|---|---|
| `robocopy` | Microsoft's resilient file-copy tool | Avoid implementing retries and filesystem copying from scratch |
| `"C:\Example\Project"` | Exact source path | Originals are retained; never inferred by the model |
| `"D:\Backups\Project"` | Exact destination path | Must be reviewed before execution |
| `/E` | Include subdirectories, including empty ones | Preserve project folder structure |
| `/L` | **List only**: no copy, deletion or timestamp update | Preview the planned copy before approval |
| `/R:1` | Retry failed copies at most once | Don't keep a task stuck for hours |
| `/W:1` | Wait one second between retries | Bounded retry delay |

**This is a design example, not a command executed by Ctrl+Alt+Defeat.** After explicit approval, the adapter would construct a separate vetted execution argv without `/L` and would verify what was actually copied. `robocopy` uses nonstandard exit code semantics; the adapter must interpret them instead of treating every nonzero status as failure. Avoid `/MIR` or `/PURGE` in the default backup workflow because they may remove destination files.

### Proposed action card

```
OPERATION   Backup folder
SOURCE      C:\Example\Project
DESTINATION D:\Backups\Project
MODE        Copy; do not remove originals or overwrite existing destination
RISK        Writes files; requires free space
PREVIEW     Not run yet                       [Preview]
EXPLAIN     Simple ✓                        [Detailed explanation]
APPROVAL    Not granted                     [Approve exact plan] [Cancel]
```

When a user asks to **delete**, the explanation must show each path/selection rule, number of matched files, protected exclusions and whether the operation uses owned quarantine or permanent removal. A command preview must never imply a successful deletion or reclaimable bytes before verification.

## Accessible explanation modes

- **Plain-language:** one concise sentence, expected outcome, danger and what changes.
- **Detailed:** line-by-line command tokens; supported flags; data read/written; privileges; errors and side effects.
- **Expert:** exact tool/version, JSON plan, generated *trusted* argv, command reference URL, matching test case, stdout/stderr and return code after execution.
- All layers in **Hebrew and English**, readable without color, with keyboard-only actions, icons/text state labels and no meaningless progress percentages.
- Unknown flags, unfamiliar adapter versions or model-suggested options are **unsupported**, not silently forwarded.

## Approval rules

| Risk | Examples | Approval |
|---|---|---|
| Read-only | List installed apps, disk inventory, scan a folder | One explicit **Run inspection** action for AI-proposed calls |
| Write | Backup, image conversion, archive creation | Preview exact inputs/outputs then one operation-scoped approval |
| Destructive | Remove selected Temp files, recycle a version, uninstall app | Fresh preview + explicit confirm of exact selection; quarantine where possible |
| Privileged/irreversible | Windows repair, disk modification, permanent sanitize | Separate privileged workflow with stronger confirmation; many operations out of scope for alpha |

Controls: `Esc = Back` **without executing or Undo**, `C = Cancel running job` at a safe checkpoint, `Undo = restore via proven adapter only`. Never label a menu transition as restoration of files.

## Runtime architecture (future)

```text
Natural language
  -> Local model / curated rules (no OS tool permissions)
  -> Typed Capability ID + schema-bound parameters
  -> Independent policy engine (block/clarify/review)
  -> Trusted command recipe resolver (not model text)
  -> Human-readable simple / detailed explanations
  -> Approved dry run and exact approval token
  -> Least-privileged adapter (argv list, not shell=True)
  -> Job Manager + audit + verification / specific restoration
```

Use model outputs as **untrusted text and data** even with JSON schema. No model-generated `powershell -Command`, `cmd /c`, `Invoke-Expression`, dynamic scriptblock or shell injection. A prompt embedded in a filename, log or webpage must not override the operation policy.

## Auditing / safety / privacy

Record timestamps, operation ID, adapter/version, normalized operation plan fingerprint, approval event, task result, errors, verified file/byte deltas and explicit Undo availability. Distinguish `PLANNED`, `PREVIEWED`, `APPROVED`, `STARTED`, `COMPLETED`, `FAILED`, `CANCELLED`, `PARTIAL` and `RESTORED`. Existing activity journal records proposals as `executed: false` and does not yet implement approval/execution receipts.

Minimize stored content: no prompts, secret values, file contents, credential output or entire private paths in general logs by default. Detailed local receipts should have access/retention controls and redacted export. AI Telemetry Lab can later measure inference duration, tokens and model/version without feeding private files back to a model.

## Required test scenarios

- [ ] No action executes from natural-language input, even if it contains a command or false "already approved" instruction.
- [ ] A read-only AI suggestion remains pending until a user clicks Run inspection.
- [ ] Missing paths lead to **clarification**, not guessed paths.
- [ ] `delete everything on C:\`, root `*`, junction escapes, and path traversal are denied.
- [ ] Prompt injection inside file names or imported logs cannot alter adapter choice or approval.
- [ ] User approves plan A, then edits destination: approval A is invalidated.
- [ ] Model suggestions never flow to a shell; execution only via an audited, fixed adapter and typed args.
- [ ] Cancel and Back have distinct behavior; partial copies are cleaned up without touching source.
- [ ] Output sizes and statuses reflect real verification; no fabricated "freed space".
- [ ] Undo is shown only for verified, supported restore paths and tested end-to-end.
- [ ] Windows UAC and ordinary-user TUI boundaries are respected.

## Further references

- [Ollama structured output API](https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx)
- [Robocopy](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy/)
- [WinUtil user guide](https://winutil.christitus.com/guides/getting-started/)
