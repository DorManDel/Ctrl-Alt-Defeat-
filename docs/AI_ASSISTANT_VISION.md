# Ctrl+Alt+Defeat — AI-assisted system operations (future milestone)

**Status:** Design goal only. No autonomous file deletion, AI-command execution, or system-wide action has been implemented.

## Product vision

Ctrl+Alt+Defeat is the trusted, local-first **execution layer** for Windows maintenance and developer utilities. A small, optional assistant helps the user discover tools, inspect the system, propose a plan, and operate the existing modules through narrow, typed actions rather than uncontrolled shell commands.

Example: "Free space on C: without touching my games or Unity projects."

1. **Understand:** Parse the request, record protected paths, and ask only for required constraints.
2. **Observe (read-only):** Call Storage Detective, inspect disk snapshots and approved system inventory adapters.
3. **Plan:** Produce specific proposed operations with estimated impact, risk, preconditions, and reversibility.
4. **Preview:** Display exact targets, a dry-run report, exclusions and potential side effects.
5. **Approve:** Require explicit, scoped user confirmation for each destructive or privileged batch.
6. **Execute:** Dispatch a validated typed operation through the job manager, with live progress and cancel checkpoints.
7. **Verify:** Measure actual outcome, store timestamps/logs, expose undo if genuinely supported.

## Security boundaries

- **Never execute arbitrary AI-generated PowerShell, CMD, Bash or Python** in the privileged system process.
- The model may only request registered, schema-validated tools. Deny by default. Validate paths *again* immediately before use; avoid junction/symlink escapes and time-of-check/time-of-use surprises.
- Explicit user approval is required for deletions, service modifications, installers and system configuration changes. The model cannot approve on the user's behalf.
- Separate normal-user UI, optional model subprocess, and narrowly privileged action adapter. Do not run third-party games or untrusted plugins as Administrator.
- Protect Git working trees, developer projects, OneDrive-synced data, active game folders, browser profiles and user-selected exclusions by default.
- Prefer supported Windows cleanup and app-uninstallation APIs; secure-erasure claims require hardware/volume-specific procedures and must not be inferred from zero-fill-and-delete.
- Every requested/approved/completed action must be independently auditable. Distinguish *predicted* from *observed* storage savings.

## Planned architecture

```text
Terminal Dashboard / User
    -> Intent Interpreter (optional local model, initially qwen2.5-coder:7b)
    -> Typed Task Planner + Policy Engine
    -> Preview / Risk / User Approval
    -> Trusted Tool Registry (storage, backup, cleanup, conversion, diagnostics)
    -> Background Job Manager (timestamps, cancellation checkpoints)
    -> Result Verifier + Audit Log + Undo where possible
```

The assistant should be removable: every operation must remain available through the ordinary CLI. External APIs and an AI Office orchestrator can be plugged in later, with privacy and provider selection under user control.

## Implementation phases

- **A0: Trusted actions.** Define operation schemas, capability permissions, dry-run previews, structured results, and test fixtures. No AI needed.
- **A1: Read-only assistant.** Route natural-language questions to diagnostics and help. Report source, confidence, and observed-versus-estimated figures.
- **A2: Guided execution.** Translate to typed tool calls, require user confirmation before changes; add cancellation, logging, and recovery tests.
- **A3: Model adapters.** Compare a compact Ollama model against optional cloud providers using AI Telemetry Lab metrics for latency, cost, token usage and quality.
- **A4: Cross-platform adapters.** Linux and macOS capability modules with platform-specific privilege handling; iOS is highly sandboxed and cannot offer equivalent system-wide maintenance.

## Release criteria

No AI feature merges to `main` until adversarial prompt-injection and path-safety tests, dry-run and approval tests, cancellation tests, and Windows smoke tests pass. Review generated commands as untrusted output. Document limitations prominently.

## Related initiatives

- **AI Office / CloudPilot:** orchestrates multiple specialist agents across local and remote models.
- **AI Telemetry Lab:** independently benchmarks token use, inference speed, latency, resource usage, estimated energy and provider cost.
- **PCM:** stores architecture, evidence, decisions and tested project handoffs.

Ctrl+Alt+Defeat remains the execution adapter, not an unrestricted agent with administrative authority.
