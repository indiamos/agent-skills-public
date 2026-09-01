#!/usr/bin/env python3
"""Helper script for the export-full skill.

Subcommands:
  find-current [<cwd>]
      Find the most recently modified JSONL session file for the current working
      directory (or <cwd> if provided) and print three KEY=VALUE lines to stdout:
          JSONL=<absolute-path>
          SESSION_START=<YYYY-MM-DD-HHMM>
          OUTPUT_DIR=<value of $EXPORT_FULL_OUTPUT_DIR, or empty string>
      Exit 1 if no JSONL file is found or if the timestamp cannot be extracted.

  timestamp <jsonl>
      Print the session start timestamp in YYYY-MM-DD-HHMM format (local time).
      Exit 1 if no timestamp is found.

  finalize <output_path> <relative_path> <description>
      Trim trailing tool-call/blank artefact lines from the output file, then
      append a summary line of the form:

          Exported to <relative_path> — <N> lines, <size>. <description>

      where <N> and <size> are computed from the file before trimming.
      Prints the constructed summary line to stdout.
      Exit 1 on error.
"""

import datetime
import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# timestamp
# ---------------------------------------------------------------------------

def _read_timestamp(jsonl_path: str) -> "str | None":
    """Return session start timestamp string, or None on failure."""
    try:
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = record.get("timestamp")
                if ts:
                    dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    return dt.astimezone().strftime("%Y-%m-%d-%H%M")
    except OSError:
        pass
    return None


def cmd_timestamp(jsonl_path: str) -> int:
    """Extract and print session start timestamp to stdout."""
    result = _read_timestamp(jsonl_path)
    if result is None:
        print(f"No timestamp found in {jsonl_path}", file=sys.stderr)
        return 1
    print(result)
    return 0


# ---------------------------------------------------------------------------
# find-current
# ---------------------------------------------------------------------------

def _resolve_output_dir(cwd: str, home: "str | None" = None) -> str:
    """Return EXPORT_FULL_OUTPUT_DIR by reading settings files, last-wins.

    Reads in order: ~/.claude/settings.json, <cwd>/.claude/settings.json,
    <cwd>/.claude/settings.local.json. The last file that defines the key wins.
    """
    if home is None:
        home = os.path.expanduser("~")

    candidates = [
        os.path.join(home, ".claude", "settings.json"),
        os.path.join(cwd, ".claude", "settings.json"),
        os.path.join(cwd, ".claude", "settings.local.json"),
    ]

    value = ""
    for path in candidates:
        try:
            with open(path) as f:
                data = json.load(f)
            found = data.get("env", {}).get("EXPORT_FULL_OUTPUT_DIR")
            if found is not None:
                value = found
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
    return value


def cmd_find_current(cwd: "str | None" = None, home: "str | None" = None) -> int:
    """Find the current session JSONL, extract its timestamp, and read output dir."""
    if cwd is None:
        cwd = os.getcwd()
    if home is None:
        home = os.path.expanduser("~")

    project_dir = cwd.replace("/", "-").replace(".", "-").replace("_", "-")
    projects_base = os.path.join(home, ".claude", "projects")
    session_dir = os.path.join(projects_base, project_dir)

    try:
        entries = os.listdir(session_dir)
    except OSError as e:
        print(f"Cannot list {session_dir}: {e}", file=sys.stderr)
        return 1

    candidates = []
    for fname in entries:
        if fname.endswith(".jsonl"):
            fp = os.path.join(session_dir, fname)
            candidates.append((os.path.getmtime(fp), fp))

    if not candidates:
        print(f"No JSONL files found in {session_dir}", file=sys.stderr)
        return 1

    candidates.sort(reverse=True)
    jsonl_path = candidates[0][1]

    session_start = _read_timestamp(jsonl_path)
    if session_start is None:
        print(f"No timestamp found in {jsonl_path}", file=sys.stderr)
        return 1

    output_dir = _resolve_output_dir(cwd, home=home)

    print(f"JSONL={jsonl_path}")
    print(f"SESSION_START={session_start}")
    print(f"OUTPUT_DIR={output_dir}")
    return 0


# ---------------------------------------------------------------------------
# finalize
# ---------------------------------------------------------------------------

def _human_size(nbytes: int) -> str:
    """Return human-readable size (nearest KB, min 1K)."""
    kb = max(1, (nbytes + 1023) // 1024)
    if kb < 1024:
        return f"{kb}K"
    return f"{(kb + 1023) // 1024}M"


# Lines at the end of an export that are artefacts of the export Bash
# invocation itself being recorded in the transcript.
_TRAILING_MD_OPENER = re.compile(r"^\*\*`")   # **`ToolName(...)`**  opener
_TRAILING_TXT_GLYPH = re.compile(r"^⏺")       # ⏺ assistant/tool glyph (txt)
_TRAILING_TXT_DESC  = re.compile(r"^  # ")    # Bash description comment (txt)
_TRAILING_MD_CLOSER = ")`**"                   # end of bold-code tool line


def _is_trailing_noise(line: str) -> bool:
    s = line.rstrip("\n")
    if not s.strip():
        return True
    if _TRAILING_MD_OPENER.match(s):
        return True
    if _TRAILING_TXT_GLYPH.match(s):
        return True
    if _TRAILING_TXT_DESC.match(s):
        return True
    if s.endswith(_TRAILING_MD_CLOSER):
        return True
    return False


def cmd_finalize(output_path: str, relative_path: str, description: str) -> int:
    """Trim trailing noise, append summary line, print summary to stdout."""
    try:
        with open(output_path) as f:
            lines = f.readlines()
    except OSError as e:
        print(f"Error reading {output_path}: {e}", file=sys.stderr)
        return 1

    # Capture stats from the file as-converted (before trimming/appending).
    line_count = len(lines)
    byte_count = sum(len(l.encode()) for l in lines)
    size = _human_size(byte_count)

    while lines and _is_trailing_noise(lines[-1]):
        lines.pop()

    home = os.path.expanduser("~")
    if relative_path.startswith(home + "/"):
        display_path = "~" + relative_path[len(home):]
    else:
        display_path = relative_path
    summary = f"Exported to {display_path} — {line_count} lines, {size}. {description}"
    lines.append("\n")
    lines.append(summary + "\n")

    try:
        with open(output_path, "w") as f:
            f.writelines(lines)
    except OSError as e:
        print(f"Error writing {output_path}: {e}", file=sys.stderr)
        return 1

    print(summary)
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1

    subcmd = sys.argv[1]

    if subcmd == "find-current":
        return cmd_find_current(sys.argv[2] if len(sys.argv) >= 3 else None)

    if subcmd == "timestamp":
        if len(sys.argv) < 3:
            print("Usage: export-session.py timestamp <jsonl>", file=sys.stderr)
            return 1
        return cmd_timestamp(sys.argv[2])

    if subcmd == "finalize":
        if len(sys.argv) < 5:
            print(
                "Usage: export-session.py finalize <output> <relative_path> <description>",
                file=sys.stderr,
            )
            return 1
        return cmd_finalize(sys.argv[2], sys.argv[3], sys.argv[4])

    print(f"Unknown subcommand: {subcmd!r}", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
