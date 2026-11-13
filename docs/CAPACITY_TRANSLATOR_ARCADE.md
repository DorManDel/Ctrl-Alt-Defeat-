# Ctrl+Alt+Defeat v0.3 — Capacity, Translator & Arcade

## Launch

Windows: double-click `CtrlAltDefeat.cmd`; it requests UAC elevation and starts the numbered menu. This remains a source-based Python application, not a compiled executable. It requires Python 3.10+. No runtime download is performed by the launcher.

## Capacity Test (bounded)

This **does not wipe the disk**. It never overwrites preexisting files. It creates an uniquely named `.winforge-capacity-...` directory, writes test data, flushes it, reads it back to verify SHA-256 hashes, and removes only its owned test files when cleanup is selected. On error it retains the test files for inspection. Verification may still be affected by drive caches or counterfeit devices; a bounded test does **not** prove the entire advertised capacity.

The Windows system drive is blocked. Tests are capped at 4096 MiB and maintain at least 5120 MiB free space at the start. Do not test an unstable drive containing important data without backup. Do not use `zeros` to verify fraudulent capacity; repeating zeros compress easily and can mask fake storage. The `random` mode provides higher-entropy data.

The interactive menu requests target folder, MiB, random/zeros mode, shows a dry run and requires typing `TEST` before any writing. It then verifies and removes its own test files. Direct CLI:

```
py -m ctrl_alt_defeat capacity-test "D:\TestFolder" --mib 64
py -m ctrl_alt_defeat capacity-test "D:\TestFolder" --mib 64 --mode random --apply --cleanup
```

After a crash or aborted test, locate `.winforge-capacity-*` and use:

```
py -m ctrl_alt_defeat capacity-cleanup "D:\TestFolder\.winforge-capacity-<id>"
```

The cleanup operation refuses unrecognized files, modified contents, missing manifests or symlinks. It may retain abandoned files for manual recovery rather than risk deletion.

### True media capacity and secure erasure are separate actions

For checking **entire** USB/SD capacity, use an established tool such as [F3](https://github.com/AltraMayor/f3) (`f3write`/`f3read`) or [FlashTester](https://github.com/Dissimilis/FlashTester), after backing up data. Full-space testing can fill a drive and disrupt apps; the Ctrl+Alt+Defeat bounded test deliberately does not do this. For securely sanitizing media, use vendor/OS-supported Secure Erase, Sanitize or crypto-erase methods, appropriate to the device and backed-up data. Writing zeros and deleting files is **not** a secure wipe of an SSD due to wear leveling, TRIM, snapshots and overprovisioning. Secure-erasure integration is not included in this release.

## Natural-language Command Translator

A small, offline, **non-AI**, whitelist-based rule matcher. It suggests read-only PowerShell / tool commands and does not execute them, so users can inspect and copy. Unrecognized requests return no command instead of inventing dangerous commands. Future versions can offer AI planning constrained to typed, approved action manifests.

## Arcade Easter Eggs

The `A` menu shows curated external projects; the games themselves are **not bundled yet**:

- Snake: [GeorgeZhukov/python-snake](https://github.com/GeorgeZhukov/python-snake), MIT, Python/curses (Windows compatibility needs testing).
- Space Invaders: [fastrgv/RetroArcade](https://github.com/fastrgv/RetroArcade), terminal-based on Windows/Linux/macOS (check license and release before any redistribution).

No third-party code is silently downloaded or run as Administrator. A future release can vendor vetted, license-compatible engines and launch arcade games unelevated.

## Repo guidance

A dedicated GitHub repository is appropriate once the user chooses the owner/name. Suggested repo: `Ctrl+Alt+Defeat`, with protected `main`, feature branches, CI tests, and original batch scripts archived under `legacy/`. This ZIP is not pushed to a repository.
