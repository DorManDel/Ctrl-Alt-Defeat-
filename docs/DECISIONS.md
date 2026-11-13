# Why we built it this way

[← Atlas](ATLAS.md) · [Home](../README.md)

These decisions preserve the story of the project, including mistakes we learned from.

| Decision | Reason | Tradeoff |
|---|---|---|
| **CLI before GUI** | Keyboard-first tools are fast to prototype and work well for diagnostics | Needs careful terminal sizing, focus management and accessible controls |
| **Two-pane UI** | Navigate modules while seeing details/status | More input and rendering states to test |
| **Persistent operation status** | A frozen screen should never be mistaken for ongoing work | Real percentages are not always knowable during filesystem scans |
| **Background tasks + cancel checkpoints** | You must be able to browse and return while scanning/copying | Cancellation cannot instantly interrupt a blocked system call |
| **Snapshots before deletion** | Our original disk mystery had no trustworthy before/after record | Logical folder sizes aren't necessarily unique allocated bytes |
| **Scoped cleanup instead of blanket deletes** | Historical batch scripts freed space but also targeted broad system areas | Some caches stay deliberately out of reach until a supported method exists |
| **Preview + user confirmation** | An elevated process must not erase data based on a vague suggestion | Adds a step to destructive workflows |
| **No arbitrary AI shell commands** | Model output can be mistaken or manipulated | Requires structured tool registry and policies first |
| **Keep old scripts archived** | Their practical history informed this project | They must be clearly marked as unsafe to run blindly |
| **Test the actual startup route** | v0.5 showed a new dashboard in tests but still launched the old menu | Startup needs integration/smoke tests, not unit tests alone |
| **Keep `main` stable** | We want a reliable public baseline | New features stay on `dev` until Windows validation |

## Our north star

**Human request → discover → scan → preview → approve → execute → verify → log.**

An optional local assistant should help explain choices, never replace explicit consent for privileged or destructive actions.
