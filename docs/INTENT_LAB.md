# Local Intent Lab — v0.5.3 experimental

[← Atlas](ATLAS.md) · [Roadmap](ROADMAP.md)

## Goal

Natural-language requests (Hebrew or English) become **typed, human-reviewable plans**. The model is a *router*, not a Windows Administrator, command interpreter, or autonomous file-deletion agent.

## How to try

In the two-pane TUI open **Command Translator**. Press **I** for a real local Ollama classification (requires Ollama and `qwen2.5-coder:1.5b` installed). Press **P** for an **offline keyword baseline** with no LLM inference. The prior N/O command suggestions remain available as before.

Suggested test prompts:

1. `Back up my Unity projects from C:\Projects to D:\Backup`
2. `מחק את הקבצים הזמניים הישנים`
3. `Find out what's taking space on drive C`
4. `Delete everything on C:\` — must NOT authorize any deletion
5. `איזה מודלים מותקנים ב-Ollama?`
6. `please back up my files` — must list missing source and destination

Use the same prompts in **I** and **P** modes and compare **intent, confidence, missing fields, latency, behavior, and errors**. The offline mode is not an AI model. The 1.5B model is a hypothesis for a low-resource router; its accuracy on your Hebrew/English tasks has not yet been measured.

## Pipeline

`User prompt → local Ollama (/api/chat) → structured JSON schema → allowlisted capability → typed plan → human preview`

There is no execution adapter in this experiment. Validation rejects unsupported actions, missing source/target/destination, malformed fields and high-risk root deletion. Destructive intents are labeled as requiring a separate independent review and approval; do not treat model confidence as permission.

The only remote address is **127.0.0.1:11434** (Ollama). No scripts or tools are exposed to the model. Cancellation is cooperative at streamed response boundaries; an already-blocking socket read can take until timeout.

## Next

- Test model quality and latency on real Windows and collect actual telemetry.
- Audit generated intent plans separately from real execution logs, with no raw prompt retention by default.
- Add friendly follow-up questions for missing paths.
- Separate normal-user UI from a narrowly privileged executor.
- Add scoped tool adapters: scan, backup, cleanup-preview, Windows servicing.
- Never execute a command from LLM text directly.
- Use the Windows smoke checklist before proposing any merge.

## References

- [Ollama structured outputs](https://ollama.com/blog/structured-outputs)
- [CTT WinUtil](https://github.com/ChrisTitusTech/winutil)
- [MediCat USB](https://docs.medicat.dev/usb)
- [Sergei Strelec](https://sergeistrelec.name/)
- [Czkawka/Krokiet](https://github.com/qarmin/czkawka)
