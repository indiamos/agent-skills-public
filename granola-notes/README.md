# granola-notes

Fetch meeting notes and transcripts from Granola (granola.ai) via its REST API.

## Context

Use this when you don't have access to Claude.AI connectors (e.g., when authenticating with Anthropic using an API key) but need to pull up a Granola meeting note, search for a transcript, or reference what was discussed in a recorded meeting. It's a thin wrapper around Granola's public REST API—it doesn't summarize or interpret notes itself, just fetches them as JSON for Claude to read.

## Usage

```sh
node ~/.claude/skills/granola-notes/granola.js list-notes [--since <ISO8601>] [--cursor <cursor>]
node ~/.claude/skills/granola-notes/granola.js get-note <note_id> [--transcript]
node ~/.claude/skills/granola-notes/granola.js get-transcript <note_id>
```

- `list-notes` returns a page of notes. Use `--since` to filter to notes created after a timestamp, and `--cursor` to page through results.
- `get-note` returns a single note's details. Pass `--transcript` to embed the transcript inline when it's small enough.
- `get-transcript` fetches the full transcript separately — use this when a note's inline transcript was omitted for size, or when you only need the transcript.

All commands print JSON to stdout. A non-zero exit and a message on stderr means the request failed (bad/missing key, rate limit, note not found).

## Configuration

| Env var | Purpose | Default |
| --------- | --------- | --------- |
| `GRANOLA_API_KEY` | Personal API key generated in Granola's app settings | none — required |

Set in your own shell environment (e.g., your shell profile, pulling the value from whatever secret manager you use). This skill does not manage or store the key; it only reads it from the environment when the script runs.

---

## Feedback

This repo is a one-way sync mirror of a private source; it isn't set up to accept pull requests. If you spot a bug or have a suggestion, please open an issue instead.

## License

This skill is licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
