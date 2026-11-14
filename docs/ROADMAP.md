# Roadmap / TDL

[← Atlas](ATLAS.md) · [Home](../README.md)

**Current development line:** v0.5.2 alpha (source build). Headless tests are not equivalent to Windows acceptance.

## Next — make the foundation trustworthy

- [ ] Windows startup, keyboard/navigation, resize and long-scan smoke tests
- [ ] True state indicators for idle/running/waiting/cancelling/failed
- [ ] End-to-end tests for every exposed module, with log and result verification
- [ ] One-click Windows executable: no Python installation needed
- [ ] Older-version manager Windows validation and protected-directory handling
- [ ] Proper screenshots and short walkthrough GIF after Windows acceptance

## Then — real useful operations

- [ ] Storage snapshots by drive, reliable allocated-byte accounting and explanations
- [ ] Verified recursive backup/restore and quarantine with recovery tests
- [ ] Targeted Windows cleanup adapters; never blanket-delete system files
- [ ] File conversion adapters with previews, progress and metadata preservation
- [ ] Optional third-party games in non-admin sessions, with license review

## Control Center organization / history

- [x] Navigation back-stack preserving screen, folder, drive selector and cursor (`Esc`), independent from active jobs
- [x] Scoped local activity journal for navigation and non-executed AI plans
- [x] Actual-data-only storage size bar view (`V`); not yet a graphical treemap
- [ ] Category sidebar like Windows Control Panel with favorites, search and command palette
- [ ] History browser: filters, task details, export, optional privacy redaction
- [ ] Versioned operation transactions, per-adapter rollback, restore tests
- [ ] Textual dashboard with Tree, DataTable, sparklines and process trends
- [ ] WizTree CSV/treemap and Sysinternals read-only adapters after licensing review
- [ ] Separate rescue/boot environment inspiration from MediCat and Strelec; no bundled ISOs

## Local Intent Lab — proof of concept

- [x] Structured Ollama intent classification using a small local model (preview only)
- [x] Offline explicitly labeled keyword baseline for comparison
- [ ] Benchmark Hebrew and English phrases on actual Windows Ollama (accuracy, latency, tokens, memory)
- [ ] Build capability registry with typed params, permission policy and robust path validation
- [ ] Preview actions with per-operation approvals, rollback policy and auditable execution plans

## Later — the small AI helper

- [ ] Catalog trusted tool capabilities and typed arguments
- [ ] Read-only local assistant for finding operations and explaining results
- [ ] Approval-based assistant actions with precise target previews
- [ ] AI Telemetry Lab integration for usage, latency, resource and cost metrics
- [ ] Cross-platform Linux/macOS adapters; iOS requires much more limited capabilities

**Merge gate:** passing local tests + Windows smoke tests + review + explicit approval before `dev` → `main`.
