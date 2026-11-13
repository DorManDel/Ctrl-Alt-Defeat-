# Historical batch-script audit

The original scripts are copied **verbatim** under `legacy/` for review only; Ctrl+Alt+Defeat never runs them.

| Script | Observed behavior | Verdict |
|---|---|---|
| 1 Delete Temporary Files | Recursive remove/recreate of `%temp%` and `C:\Windows\Temp`; recursive `takeown` | Unsafe, replace with scoped age-based preview |
| 2 Delete Log Files | `cd/` then recursive `del *.log /a /s /q /f` | Dangerous, reject |
| 3 Delete WU Cached Files | Stop multiple update services; delete/recreate entire `SoftwareDistribution` | Dangerous, use supported maintenance tools |
| 5 Disable Prefetch | Elevate via generated VBS; stop and disable SysMain through registry | System configuration, not cleanup; exclude |
| 6 Delete Prefetch | Recursive remove `C:\Windows\Prefetch` | Exclude |
| 6 Delete SoftwareDistribution Download | Delete files/subfolders of Windows Update Download cache | Unsafe without update-state verification |
| 6 Delete WU old stuff-SoftwareD Download | Delete entire Update Download folder | Unsafe without update-state verification |
| Delete SoftwareDistribution Download | Duplicate of first Update Download removal script | Deduplicate; do not execute |

These scripts are not dependencies of Ctrl+Alt+Defeat. Do not use them for automated cleanup.
