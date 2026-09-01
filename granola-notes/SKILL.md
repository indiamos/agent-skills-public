---
name: granola-notes
description: "Fetch meeting notes and transcripts from Granola (granola.ai) via its REST API. Use when: pulling up a recent Granola meeting note, searching for a transcript, or referencing what was discussed in a recorded meeting."
---

Fetch notes and transcripts from Granola using its public REST API.

## Setup

Requires `GRANOLA_API_KEY` in the environment (see README for one-time setup). If it's unset, the script exits with an explanation on stderr. Relay that message and ask the user to set it rather than guessing where the key might be stored.

## Usage

```sh
node ~/.claude/skills/granola-notes/granola.js list-notes [--since <ISO8601>] [--cursor <cursor>]
node ~/.claude/skills/granola-notes/granola.js get-note <note_id> [--transcript]
node ~/.claude/skills/granola-notes/granola.js get-transcript <note_id>
node ~/.claude/skills/granola-notes/granola.js find-note --title <substring> [--since <ISO8601>] [--transcript]
```

- When the user names a note by title (e.g., "today's note titled X", "the Y meeting note"), prefer `find-note` over `list-notes` + manual matching. `find-note` resolves the title to a note and fetches it in one call. It's a case-insensitive substring match; `--since` defaults to the start of the current UTC day if omitted. Zero or multiple matches print candidates to stderr instead of guessing.
- `find-note` can't filter by folder. The API has no documented folder query parameter, and `list-notes` doesn't return folder membership (only `get-note` does). If the user names a folder, use it as human context to sanity-check the match, not as a filter.
- `list-notes` returns a page of notes (`notes`, `hasMore`, `cursor`). Use `--since` to filter to notes created after a timestamp, and `--cursor` to page through results. Fall back to this when `find-note` doesn't fit (e.g., browsing recent notes with no title in hand).
- `get-note` returns a single note's details (`id`, `title`, `owner`, `summary`). Pass `--transcript` to embed the transcript inline when it's small enough.
- `get-transcript` fetches the full transcript separately — use this when a note's inline transcript was omitted for size, or when you only need the transcript.

All commands print JSON to stdout on success. A non-zero exit means the request failed; the stderr message identifies the cause:

- `429` (rate limited): back off and retry — see Notes below for the schedule.
- `401`/`403` (bad or missing key): halt and tell the user their `GRANOLA_API_KEY` is invalid — do not retry, since the same key will fail again.
- `404` (note not found): halt and tell the user the note ID wasn't found — do not retry.
- Any other error: halt and relay the stderr message to the user.

## Notes

- Rate limits: 25 requests/5s burst, 300 requests/minute sustained. On `429`, wait 5 seconds and retry, doubling the wait on each subsequent `429`, up to 3 attempts total. If the 4th attempt still returns `429`, halt and tell the user the API is rate-limiting persistently — because indefinite silent retries burn tool calls without making progress.
- This talks to Granola's own API, not any account-level connector. It works regardless of which Claude auth method (API key vs. subscription login) the current session is using.
