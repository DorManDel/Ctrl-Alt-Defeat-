# Ctrl+Alt+Defeat v0.2 planning

## Shipped
- Windows one-click `.cmd` wrapper with UAC elevation request
- Source-based application menu, no manual CLI startup commands
- Read-only disk scans and snapshot comparison
- Confirmed single-file copy and backup with SHA-256 validation
- Legacy batch scripts archived, never executed

## Next iteration
- Self-contained signed Windows executable (no Python prerequisite)
- Full-screen Textual keyboard TUI with notifications and cancel support
- Safe cleanup allowlists, dry-run, per-item confirmation, quarantine where possible
- Built-in operation log and rollback capabilities where applicable
- Windows-specific adapters for OS cleanup; later Linux/macOS adapters
- Native folder-to-folder robust copy, incremental backup and converters

## Safety
Running as Administrator increases the impact of mistakes. Every destructive operation must be allowlisted, reviewed, logged and separately approved. Never automatically execute `legacy/*.bat`, disable SysMain, or delete Windows directories recursively.
