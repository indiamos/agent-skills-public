# export-full

Export a Claude Code conversation from its raw JSONL session file to a human-readable transcript.

## Context

Claude Code's built-in `/export` only exports what's in the current context window. Long conversations get compacted automatically, which means early history is silently missing from that output. This skill reads the raw JSONL session file directly, capturing the full conversation regardless of how much compaction has occurred. Works on any past session, not just the current one.

## When to use this vs. built-in `/export`

- **`/export-full`** — reads the raw JSONL file, so it includes the full conversation history even if parts have been compacted. Works on any session (current or past).
- **Built-in `/export`** — exports only what's visible in the current context window. Faster but may miss earlier history in long conversations.

## Usage

```
/export-full [session-id-or-path] [output-path]
```

- No arguments: exports the current session to a file in the output directory.
- One argument: either a session UUID/path (exports to output dir) or an output path (exports current session to that path).
- Two arguments: session reference + output path.

## Configuration

| Env var | Purpose | Default |
| --------- | --------- | --------- |
| `EXPORT_FULL_OUTPUT_DIR` | Directory where exported transcripts are saved | current working directory |

Set in your Claude settings. Project-level values override user-level; `.local.json` overrides `.json`:

- `~/.claude/settings.json` (user-level)
- `.claude/settings.json` in a project directory (project-level)
- `.claude/settings.local.json` in a project directory (project-local, highest precedence)

```json
{
  "env": {
    "EXPORT_FULL_OUTPUT_DIR": "~/conversations"
  }
}
```

Output files are named `<session-start-timestamp>-<brief-topic>.md`.

---

## Feedback

This repo is a one-way sync mirror of a private source; it isn't set up to accept pull requests. If you spot a bug or have a suggestion, please open an issue instead.

## License

This skill is licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

## Acknowledgments

- <https://github.com/afbreilyn/afb-tdd>
- <https://github.com/github/spec-kit>
- <https://github.com/ianmcnally/code-reviewer>
- <https://github.com/kenjudy/pdca-framework>
- <https://gitlab.com/phillippitts/agent-professional-review-pipeline>
