---
name: session-notify
description: Install, inspect, repair, update, or remove Windows completion notifications for Codex CLI in VS Code WSL, including clicking a toast to return to its existing terminal.
---

Use the bundled controller at `../../install.py`, resolved relative to this skill directory. Read `../../README.md` for environment requirements and installation steps.

- Inspect with `python3 <plugin-root>/install.py status`.
- For an installation or repair requested by the user, run `install --dry-run`, then `install`. The installer detects the Windows user, WSL distribution, runtime location, and a live VS Code IPC socket. An existing unrelated `notify` hook requires the user's authorization to replace it; use `--replace-notify` only within that authorization.
- Remove with `uninstall` only when the user requests removal; `uninstall --dry-run` previews the owned settings and registrations.
- After a change, verify the user service and fresh terminal-window records. Treat backend `terminal-focused` and native `activated` as separate results. For click issues, inspect `~/.codex/session-notify/events.jsonl` and `%LOCALAPPDATA%\CodexSessionNotify\native-focus.jsonl`.

Preserve the existing conversation: select its original terminal; do not open an editor, new terminal, or a new Codex process. Keep the Windows helper invisible and preserve maximized window state. Stored session metadata can say `source=vscode` even when a session was resumed in the CLI; use live CLI ancestry instead. The installer configures Bash and Zsh so ordinary `codex` launches in new terminals use an isolated CLI and direct notification hook; this supports multiple CLI terminals sharing a cwd. Existing shells and sessions must be reopened/resumed. Unmanaged shared-daemon launches still require one interactive CLI per cwd. If association is ambiguous, report the limitation rather than choosing an arbitrary terminal.

A packaged notification service stays installed across Codex sessions. Enabling or disabling this skill plugin does not start or stop that service; use the controller for its lifecycle.
