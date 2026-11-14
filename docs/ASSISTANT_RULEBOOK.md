# Global AI Assistant — Permission Rulebook

> **Design review / experimental:** A rule here is not an enabled operation. Code and Windows acceptance are needed before any execution.

[← Project Atlas](ATLAS.md) · [AI Action Protocol](AI_ACTION_PROTOCOL.md) · [Capability Plan](CAPABILITY_PLAN.md)

## Principle

**Model output is a proposal, not authorization.** The assistant can classify a request and navigate to a relevant screen, but it cannot run raw PowerShell, escalate privileges, or confirm its own proposal. Unknown capabilities are denied by default.

## Current scope

| Intent | AI permission | What happens |
|---|---|---|
| `scan_storage` | Preview + user approval | User selects an exact existing folder. After preview and approval, the trusted read-only scanner may run. |
| `backup_files` | Navigate / clarify only | Open File Operations and ask for exact source and destination; no AI-controlled backup yet. |
| `copy_files` | Navigate / clarify only | Open File Operations; separately approved manual copying is independent of AI. |
| `clean_temp` | Navigate only | Show the limited Temp preview; AI cannot confirm deletion. |
| `delete_files` | Navigate only for safe requests; deny drive-root/wildcard targets | Never dispatch arbitrary deletion from a model. |
| `inspect_windows_updates` | Navigate only | Diagnostics only; no servicing changes. |
| `list_ollama_models` | Navigate only | Model inspection area; no automatic model removal. |
| `unknown` | Block | Ask for clarification or show supported capabilities. |

## Policy outcomes

- **BLOCKED:** unsafe, unknown, forbidden or inconsistent request. Nothing starts.
- **CLARIFY:** missing details or low confidence. Can offer navigation to a benign tool, never execution.
- **NAVIGATE_ONLY:** change screens, show explanations and preview options; does not perform the tool operation.
- **PREVIEW_ALLOWED:** prepare a permitted read-only scan. A new, explicit approval is required to start it.

## What must be enforced outside the LLM

1. Known typed capability IDs, validated parameter schemas, canonical risk levels; never trust a model's claimed risk or confidence as permission.
2. Verify source, destination, paths, permissions, active files and junction/symlink safety *at time of execution*. Reject drive-root/wildcard deletion and changed targets.
3. Bind approval to **exact plan + normalized targets + adapter version + expiry**; changes invalidate prior approval.
4. Use trusted adapters with fixed options and argument arrays, never model-generated shell code or `shell=True`.
5. Enforce limits on file count, bytes, retry duration and number of running jobs.
6. Separate `Esc` (navigation) from `Cancel` (stop at safe checkpoint) and `Undo` (only where restoration is verified).
7. Minimal timestamped audit logs; do not store raw prompts, passwords, or file contents in general logs. Redact on export.
8. External tools require provenance, version detection, licensing review and separate consent for privileged actions.
9. Show actual job state and verified results; never invent recovered bytes, successful actions or rollback availability.

## Unsafe or unsupported categories

No autonomous raw shell execution, credentials extraction, serial cracking, disk sanitization, registry/boot alteration, antivirus disabling, or unattended installer/network-script execution. Authorized recovery/inventory ideas may be evaluated later as separate scoped tools.

## Rule extension checklist

For every new AI-facing capability: typed schema → human explanation → trusted adapter → preview → exact approval → revalidation → safe execution → verification → audit → Windows CI + manual smoke tests. New entries in the planning catalog **do not** grant permissions.

## Example

`"גבה את הפרויקט שלי"` → `backup_files` → **CLARIFY** source + destination → suggested File Operations screen → **no operation executed**.

`"מחק את כונן C"` → destructive ambiguous/root request → **BLOCKED / no AI action**.

`"סרוק את תיקיית הפרויקט"` → `scan_storage` → user selects folder → **PREVIEW** → user approves same path → trusted read-only scan → audited result.

The full implementation and tests live in the experimental local preview until reviewed and validated on Windows.
