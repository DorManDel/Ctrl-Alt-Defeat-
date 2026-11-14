# Ctrl+Alt+Defeat — Control Center blueprint

[← Atlas](ATLAS.md) · [Intent Lab](INTENT_LAB.md) · [Roadmap](ROADMAP.md)

## Goal

**One place to inspect, understand, and manage a Windows machine.** Group operations like Windows Control Panel, retain navigation/history like a game UI stack, and add practical visualizations without surrendering execution control to an LLM.

## Proposed navigation (not yet all implemented)

| Sector | Pages and useful visuals | Adapter opportunities | Status |
|---|---|---|---|
| **Overview** | CPU, RAM, disk, health, recent jobs, alerts | Windows performance counters, psutil | Design |
| **Storage & Cleanup** | Drive tree, folder bars, treemap, storage deltas, safe cleanup plans | WizTree CSV / image export, Czkawka | Bar view prototype; adapters proposed |
| **Files & Recovery** | File copy/backup queue, snapshots, restore/quarantine | robocopy, 7-Zip, Windows File History | Single-file verified copy exists; recovery proposed |
| **Processes & System** | Process tree, CPU/RAM plots, events, service status | Sysinternals Process Explorer / Procmon | Proposed |
| **Software & Updates** | Installed apps, updates, cache inspection, repair recipes | WinGet, CTT WinUtil, DISM | Partial read-only tools; integrations proposed |
| **Devices & Boot** | Drives/USB health, boot recovery, hardware inventory | MediCat & Sergei Strelec design references, SMART tools | Future, separate recovery environment |
| **AI Operator** | Request → intent → required fields → safe preview | Ollama local JSON schema, later plugin adapters | Preview-only proof of concept |
| **History & Settings** | Navigation stack, activity journal, job log, tests, modules | Local JSONL / SQLite | Stack + journal prototype |

## Screens and state

```text
Navigation stack:  Home → Storage → D:\ → Games → Details
                       [Esc]  ←    ←        ←

Job engine:         QUEUED → RUNNING → COMPLETED / FAILED / CANCELLED
                    (independent from which page is visible)

AI plan:            REQUEST → INTENT → VALIDATE → PREVIEW → APPROVAL → TOOL
                                 [Currently stops before TOOL]
```

**Back is not Undo.** Esc restores the prior screen and folder without canceling a scan. Undo of a completed file operation requires the *specific adapter* to provide a verified inverse operation (e.g., restoring an owned quarantined file or a backup). Arbitrary deletion, disk formatting, registry changes and secure erase do not have a universal undo mechanism.

## Visualizations

- **Now:** `V` in Storage Detective toggles list/bars after an actual completed scan for that folder. Bars represent **logical sizes**, not unique allocated bytes; no fabricated percentage.
- **Next:** Textual `Tree`, `DirectoryTree`, `DataTable`, `Sparkline`, `ProgressBar`, `Log`, with keyboard/mouse, filters and search.
- **Storage adapter:** WizTree documents CLI CSV and treemap export; can consume *user-installed* exports with a documented adapter, without silently bundling licensed components.
- **Process adapter:** Microsoft Sysinternals Process Explorer displays ownership/handles, while Procmon captures file/registry/process events. Default capture should be explicitly started, bounded and stoppable because it can produce substantial logs.

## Operation safety & privacy

1. Present a **typed operation plan**, never arbitrary executable model text.
2. Identify precise targets and scope. Block dangerous or ambiguous roots.
3. Show files, estimated bytes, and a dry-run preview when appropriate.
4. Obtain independent confirmation before any write/deletion.
5. Execute via tested, least-privilege adapter (never give the model an Administrator shell).
6. Verify outputs and actual freed disk space; preserve timestamps and a local operation record.
7. Offer Undo only when tested and supported by the adapter.

## Later experiments

Recovery of one's **own accounts, credentials or owned software license information** should use vendor-supported export/recovery APIs and explicit consent. Do not embed indiscriminate credential dumping or license cracking tools in the default utility. Separate privileged diagnostics from ordinary-user visualizations and third-party games.

## Sources for design

- [Textual widgets](https://textual.textualize.io/widget_gallery/)
- [WizTree documented CLI exports](https://diskanalyzer.com/guide)
- [Process Explorer](https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer)
- [Process Monitor](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon)
- [CTT WinUtil](https://github.com/ChrisTitusTech/winutil)
- [MediCat USB](https://docs.medicat.dev/usb) and [Sergei Strelec](https://sergeistrelec.name/)
