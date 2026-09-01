---
name: export-full
description: Export a Claude Code conversation from its raw JSONL session file to a human-readable transcript matching the /export format. Use when the user wants to export a conversation (current or past), convert a session JSONL, or create a detailed transcript that includes compacted history.
argument-hint: "<session-id-or-path> <output-path>"
---

# Export Full Conversation Transcript

Convert a Claude Code JSONL session file into a human-readable text transcript that closely matches the built-in `/export` format.

## When to use `/export-full` vs. built-in `/export`

- **`/export-full`**: Exports from the raw JSONL file, which includes the ENTIRE conversation history even if parts have been compacted. Works on any session (current or past). Produces a more complete transcript.
- **Built-in `/export`**: Exports only the conversation visible in the current context window (since the last compaction). Faster but may miss earlier parts of long conversations.

## Step 0: Verify Correct Invocation

Inspect the most recent user message in the conversation history.

- **If the user typed `/export` (not `/export-full`)**:
  - **STOP**. Do not proceed.
  - Tell the user: "`/export` is the built-in Claude Code command and runs without my involvement. `/export-full` (this skill) exports from the raw JSONL file and includes compacted history. It sounds like you may have wanted the built-in command."
  - Ask: "Did you mean to run `/export-full`? (yes/no)"
  - Wait for user response before continuing.
  - If user says "no": Halt. Remind them to re-type `/export` themselves.
  - If user says "yes": Proceed to the next step.

- **If the user typed `/export-full`**: Proceed to the next step.

## How to find the JSONL file

Claude Code stores session JSONL files at:

```
~/.claude/projects/<project-dir>/<session-uuid>.jsonl
```

The `<project-dir>` is derived from the working directory by replacing `/`, `.`, **and** `_` with `-`. For example:

- cwd `/Users/alice/repos` -> project dir `-Users-alice-repos`
- cwd `/Users/alice/repos/my-service` -> project dir `-Users-alice-repos-my-service`
- cwd `/Users/alice/.claude` -> project dir `-Users-alice--claude` (dot in `.claude` → extra `-`)
- cwd `/Users/alice/repos/my_project` -> project dir `-Users-alice-repos-my-project` (underscore → `-`)

### If the user provides a session UUID or partial UUID:

1. Glob for `~/.claude/projects/*/<uuid>*.jsonl`

### If the user says "the current session" or "this conversation":

1. Find the most recently modified JSONL file in the current project directory (see "Finding the current session" section below)
2. This will be the currently running session - the JSONL file can be read even while being written to

### If the user provides a .jsonl file path directly:

1. Use that path as-is.

### If the user says "the last conversation" or gives a description:

1. List JSONL files in the relevant project directory sorted by modification time
2. Read the first few lines of candidates to find the matching session (check for user messages that match the description)

## Conversion

Run the conversion script that lives alongside this skill:

```bash
python3 ~/.claude/skills/export-full/jsonl-to-transcript.py <input.jsonl> <output.md>
```

Store the exit code. If the script exits non-zero or produces no output file,
report the error output to the user and halt. Do not proceed to post-processing.

The script auto-detects format from the output file extension:

- `.md` → **Markdown format** (default for new exports)
- anything else → **txt format** (matches built-in `/export` style)
- Override with `--format txt` or `--format md`

**Markdown format** (`.md` output):

- Assistant text rendered as-is (it's already Markdown — headers, bold, bullets all work)
- Tool calls shown as **`ToolName(args)`** inline bold code
- Tool results wrapped in fenced ` ```text ``` ` blocks so content isn't misinterpreted as Markdown
- Thinking blocks as `> *[thinking] ...*` blockquotes
- User turns separated by `---` horizontal rules with `**❯ User**` heading
- Session banner as a blockquote

**txt format** (matches `/export`):

- `❯` for user messages
- `⏺` for assistant text and tool calls
- `⎿` for tool results (truncated to 200 chars/line, 30 lines max)
- `[thinking]` for thinking blocks (first 200 chars)
- Bash tool descriptions shown as `# comment` lines

Both formats skip noise: progress events, API retries, file snapshots, queue operations

## Arguments

Bind SESSION_REF and OUTPUT_PATH from `$ARGUMENTS`:

**No arguments**: SESSION_REF = current session (most recently modified JSONL
in the current project directory). OUTPUT_PATH = unset (derive below).

**One argument**:

- If the argument ends in `.jsonl` or looks like a UUID: SESSION_REF = argument.
  OUTPUT_PATH = unset (derive below).
- If the argument ends in `.md` or `.txt` or contains `/`: SESSION_REF = current
  session. OUTPUT_PATH = argument.
- If ambiguous: ask the user "Is `<arg>` a session ID or an output path?"
  Wait for response before continuing. Bind accordingly.

**Two arguments**: SESSION_REF = first argument. OUTPUT_PATH = second argument.

**STOP gate:** If SESSION_REF cannot be determined after the above, ask:
"Which session should I export? Provide a UUID, a .jsonl path, or say
'current'." Wait for the response before continuing.

Store the resolved values as SESSION_REF and OUTPUT_PATH and carry them through
all remaining steps.

## Extracting the session start timestamp

After resolving the JSONL path, extract the timestamp using the helper script:

```bash
python3 ~/.claude/skills/export-full/export-session.py timestamp <jsonl_path>
```

Store the result as SESSION_START (e.g., `2026-03-17-1535`).

**STOP gate:** If the command exits non-zero or produces no output, report the
error and halt. Do not substitute today's date.

### Combining with JSONL discovery (current session)

Use the `find-current` subcommand:

```bash
python3 ~/.claude/skills/export-full/export-session.py find-current
```

Output is three KEY=VALUE lines:

```
JSONL=<absolute-path>
SESSION_START=<YYYY-MM-DD-HHMM>
OUTPUT_DIR=<resolved value, or empty>
```

This call is pre-approved via `Bash(python3 ~/.claude/skills/export-full/*)`.
Parse JSONL, SESSION_START, and OUTPUT_DIR from its output.

## Choosing the output directory

**If OUTPUT_PATH is already bound** (user provided it as an argument): skip this section entirely.

**If OUTPUT_PATH is unset**, use the OUTPUT_DIR value from the `find-current`
output (already in hand from the JSONL discovery step above).

- If OUTPUT_DIR is non-empty: use it as the output directory.
- If OUTPUT_DIR is empty: use the current working directory (`$PWD`).

Construct the full path: `<OUTPUT_DIR>/<SESSION_START>-<brief-topic>.md`

Use a brief topic slug (2–5 words, kebab-case) derived from the conversation content.

To set a persistent default, add to your Claude settings:

```json
{
  "env": {
    "EXPORT_FULL_OUTPUT_DIR": "~/conversations"
  }
}
```

## Finding the current session

Use the `find-current` subcommand (see "Combining with JSONL discovery" above).
It derives the project directory from the cwd, finds the most recently modified
`.jsonl` file, and returns JSONL path + SESSION_START + OUTPUT_DIR in one call.

## Safety Checks (before conversion)

1. **Verify JSONL exists and is readable**:

   **STOP gate:** If the JSONL file does not exist at the resolved path,
   report: "Session file not found: `<path>`." List the three most recently
   modified `.jsonl` files in the project directory and halt.

   **STOP gate:** If the JSONL file exists but is empty (0 bytes), report:
   "Session file is empty: `<path>`. Nothing to export." and halt.

2. **Check output file**:
   - If output path already exists: Show size and first line, ask "Overwrite? (y/n)"
   - If user says no: Prompt for new output path

3. **Create output directory**:
   - The conversion script creates the output directory automatically; no separate `mkdir` call needed.

## After conversion

1. Trim trailing artefact lines and append the summary in one command.
   Inline the absolute output path directly — do not use shell variables (see
   "Two separate calls" below for the reason):

   ```bash
   python3 ~/.claude/skills/export-full/export-session.py finalize /absolute/path/to/output.md /absolute/path/to/output.md "One-sentence topic description."
   ```

   Arguments:
   - First positional — absolute path to the converted file (for reading/writing).
   - Second positional — same absolute path; the script normalizes it to `~/...` for display.
   - Third positional — one sentence describing the conversation subject.

   The script trims trailing blank/tool-call lines left by the conversion,
   counts lines and computes file size from the as-converted file, then writes:

   ```
   Exported to ~/<relative-path> — <N> lines, <size>. <topic sentence>.
   ```

   It prints that summary line to stdout.

   **STOP gate:** If the command exits non-zero, report the error and halt.
   Do not proceed to step 2 with a potentially corrupted file.

   ✅ `python3 ~/.claude/skills/export-full/export-session.py finalize /Users/me/out.md /Users/me/out.md "Conversation about improving the export-full skill."`

   ❌ Prepending `OUTPUT=...` on a separate line, or omitting the topic sentence.

   ### Two separate calls (each pre-approved)

   Run conversion and finalize as **two separate Bash calls**. Each call must
   **start with `python3 ~/.claude/skills/export-full/...`** so it matches the
   `Bash(python3 ~/.claude/skills/export-full/*)` allowlist rule. Inline the
   absolute paths directly — do NOT set shell variables like `OUTPUT=...` or
   `JSONL=...` on a preceding line, because each Bash tool call runs in its own
   shell (so the variable would be undefined anyway) AND the leading assignment
   causes the command to no longer start with `python3`, which breaks the
   allowlist match and triggers an approval prompt.

   **Call A — convert** (substitute the real absolute paths):

   ```bash
   python3 ~/.claude/skills/export-full/jsonl-to-transcript.py /absolute/path/to/session.jsonl /absolute/path/to/output.md
   ```

   **Call B — finalize** (only if Call A succeeds; repeat the output path as the
   second argument so the script can normalize it to `~/...` for display):

   ```bash
   python3 ~/.claude/skills/export-full/export-session.py finalize /absolute/path/to/output.md /absolute/path/to/output.md "One-sentence topic description."
   ```

   Do NOT chain them with `&&`, `;`, or backslash-newlines into a single
   multi-line command — the allowlist `*` does not match across newlines or
   statement separators.

2. Report the summary line (printed by `finalize`) to the user in chat.
3. Mention that for interactive/GUI exploration of chat history, the user can also try [claude-code-log](https://github.com/daaain/claude-code-log)
