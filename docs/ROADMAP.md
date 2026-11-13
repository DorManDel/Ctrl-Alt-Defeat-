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

## Later — the small AI helper

- [ ] Catalog trusted tool capabilities and typed arguments
- [ ] Read-only local assistant for finding operations and explaining results
- [ ] Approval-based assistant actions with precise target previews
- [ ] AI Telemetry Lab integration for usage, latency, resource and cost metrics
- [ ] Cross-platform Linux/macOS adapters; iOS requires much more limited capabilities

**Merge gate:** passing local tests + Windows smoke tests + review + explicit approval before `dev` → `main`.
