#!/usr/bin/env python3
"""Convert a Claude Code JSONL session transcript to a human-readable file.

Two output formats:
  txt (default): matches built-in /export style with unicode glyphs
  md:            Markdown — assistant text renders natively, tool calls/results
                 are fenced code blocks so they don't get interpreted as Markdown

Usage:
    python3 jsonl-to-transcript.py <input.jsonl> [output.txt|output.md] [--format txt|md]
    python3 jsonl-to-transcript.py <input.jsonl>          # prints to stdout (txt format)

Default format is Markdown. Format is inferred from the output file extension
(.txt -> txt, anything else -> md) and can be overridden with --format.
"""

import json
import os
import sys
import re
import textwrap


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_LINE_LEN = 200          # truncate individual output lines (txt format)
MAX_RESULT_LINES = 30       # max lines shown per tool result
MAX_THINKING_CHARS = 200    # how much of a thinking block to show


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WRAP_WIDTH = 80          # match built-in /export line width


def truncate_line(line: str, maxlen: int = MAX_LINE_LEN) -> str:
    if len(line) <= maxlen:
        return line
    return line[:maxlen] + "..."


def wrap_text_block(text: str, first_prefix: str, continuation_prefix: str) -> str:
    """Wrap a multi-paragraph text block to WRAP_WIDTH.

    Each paragraph is wrapped independently; blank lines between paragraphs are
    preserved.  Lines that look like code/lists (start with spaces, -, *, ``)
    are passed through unwrapped.
    """
    out_lines = []
    paragraphs = text.split("\n")
    for para in paragraphs:
        stripped = para.rstrip()
        # Pass through blank lines, code-like lines, and list items as-is
        if not stripped or stripped.lstrip().startswith(("- ", "* ", "` ", "```", "  ")):
            out_lines.append(stripped)
            continue
        # Wrap the paragraph
        available = WRAP_WIDTH - len(first_prefix) if not out_lines else WRAP_WIDTH - len(continuation_prefix)
        wrapped = textwrap.wrap(stripped, width=WRAP_WIDTH - len(continuation_prefix))
        out_lines.extend(wrapped)
    if not out_lines:
        return ""
    result_lines = []
    for idx, line in enumerate(out_lines):
        prefix = first_prefix if idx == 0 else continuation_prefix
        result_lines.append(prefix + line if line else "")
    return "\n".join(result_lines)


def format_tool_name(raw_name: str) -> str:
    """Shorten MCP tool names:  mcp__atlassian__jira_tech_get_issue -> atlassian/jira_tech_get_issue"""
    if raw_name.startswith("mcp__"):
        parts = raw_name.split("__", 2)
        if len(parts) == 3:
            return f"{parts[1]}/{parts[2]}"
        return raw_name[5:]
    return raw_name


def summarise_tool_input(raw_name: str, inp: dict) -> str:
    """Build a concise argument summary for a tool call, matching /export style.

    /export uses short positional-looking args, not key=value.
    Examples:
        Read(accounting-integrations/CLAUDE.md)
        Bash(go test ./... 2>&1)
        Grep(pattern, path)
        Task(Explore AIS/Xero/EOR codebase)
    """
    name = raw_name  # raw_name is the original tool name before format_tool_name

    if name == "Bash":
        cmd = inp.get("command", "")
        if len(cmd) > 80:
            cmd = cmd[:77] + "..."
        return cmd
    if name == "Read":
        fp = inp.get("file_path", "")
        # Strip common prefixes to shorten
        for prefix in [os.path.expanduser("~/repos/"), "/Users/"]:
            if fp.startswith(prefix):
                fp = fp[len(prefix):]
                break
        parts = [fp]
        if inp.get("offset"):
            parts.append(f"offset={inp['offset']}")
        if inp.get("limit"):
            parts.append(f"limit={inp['limit']}")
        return ", ".join(parts)
    if name == "Write":
        fp = inp.get("file_path", "")
        for prefix in [os.path.expanduser("~/repos/"), "/Users/"]:
            if fp.startswith(prefix):
                fp = fp[len(prefix):]
                break
        return fp
    if name == "Edit":
        fp = inp.get("file_path", "")
        for prefix in [os.path.expanduser("~/repos/"), "/Users/"]:
            if fp.startswith(prefix):
                fp = fp[len(prefix):]
                break
        return fp
    if name == "Glob":
        pat = inp.get("pattern", "")
        path = inp.get("path", "")
        if path:
            return f"{pat}, {path}"
        return pat
    if name == "Grep":
        pat = inp.get("pattern", "")
        path = inp.get("path")
        if path:
            return f"{pat!r}, {path}"
        return repr(pat)
    if name == "WebFetch":
        return inp.get("url", "")
    if name == "WebSearch":
        return inp.get("query", "")
    if name == "Task":
        desc = inp.get("description", "")
        return desc
    if name == "TaskOutput":
        return "..."

    # MCP / unknown tools: show non-ctx params as key=value
    keys = [k for k in inp if k != "ctx"][:4]
    parts = []
    for k in keys:
        v = inp.get(k)
        if v is None:
            continue
        vs = str(v)
        if len(vs) > 60:
            vs = vs[:57] + "..."
        parts.append(f"{k}={vs!r}" if isinstance(v, str) else f"{k}={v}")
    return ", ".join(parts)


def format_tool_result_content(content) -> list[str]:
    """Return a list of display lines for a tool_result content field."""
    if content is None:
        return ["(no output)"]
    if isinstance(content, list):
        # content can be a list of {type, text} blocks
        texts = []
        for block in content:
            if isinstance(block, dict):
                texts.append(block.get("text", block.get("content", str(block))))
            else:
                texts.append(str(block))
        raw = "\n".join(texts)
    else:
        raw = str(content)

    lines = raw.splitlines()
    out = []
    for line in lines[:MAX_RESULT_LINES]:
        out.append(truncate_line(line))
    if len(lines) > MAX_RESULT_LINES:
        out.append(f"     ... +{len(lines) - MAX_RESULT_LINES} more lines")
    return out


# ---------------------------------------------------------------------------
# Skippable message types
# ---------------------------------------------------------------------------

SKIP_TYPES = {"file-history-snapshot", "progress", "queue-operation"}


def should_skip(record: dict) -> bool:
    if record.get("type") in SKIP_TYPES:
        return True
    # Skip system-level API errors (retries, etc.)
    if record.get("type") == "system" and record.get("subtype") == "api_error":
        return True
    # Skip meta user messages (local-command-caveat wrappers)
    if record.get("isMeta"):
        return True
    msg = record.get("message", {})
    content = msg.get("content", "")
    if isinstance(content, str):
        stripped = content.strip()
        # Skip empty or noise-only messages
        if stripped in (
            "<local-command-stdout></local-command-stdout>",
            "",
        ):
            return True
        if stripped.startswith("<local-command-caveat>"):
            return True
    return False


# ---------------------------------------------------------------------------
# TXT format (matches built-in /export style)
# ---------------------------------------------------------------------------

def convert_txt(input_path: str, out):
    banner_printed = False
    session_id = os.path.basename(input_path).removesuffix(".jsonl")
    out.write(f"claude --resume {session_id}\n")

    tool_uses: dict[str, str] = {}

    with open(input_path) as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            if should_skip(record):
                continue

            rec_type = record.get("type", "")
            msg = record.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content", "")

            if not banner_printed and rec_type == "user" and record.get("version"):
                version = record.get("version", "")
                model = msg.get("model", "")
                cwd = record.get("cwd", "")
                out.write(f"\n \u2590\u259b\u2588\u2588\u2588\u259c\u258c   Claude Code v{version}\n")
                if model:
                    out.write(f"\u259d\u259c\u2588\u2588\u2588\u2588\u2588\u259b\u2598  {model}\n")
                else:
                    out.write(f"\u259d\u259c\u2588\u2588\u2588\u2588\u2588\u259b\u2598\n")
                out.write(f"  \u2598\u2598 \u259d\u259d    {cwd}\n\n")
                banner_printed = True

            if rec_type == "user" and role == "user":
                if isinstance(content, str):
                    text = content.strip()
                    if not text:
                        continue

                    cmd_match = re.search(r"<command-name>(.*?)</command-name>", text)
                    if cmd_match:
                        cmd = cmd_match.group(1)
                        if not cmd.startswith("/"):
                            cmd = "/" + cmd
                        args_match = re.search(r"<command-args>(.*?)</command-args>", text, re.DOTALL)
                        args = args_match.group(1).strip() if args_match else ""
                        line = f"{cmd} {args}".rstrip()
                        out.write(f"\n\u276f {line}\n")
                        continue

                    stdout_match = re.search(
                        r"<local-command-stdout>(.*?)</local-command-stdout>", text, re.DOTALL
                    )
                    if stdout_match:
                        stdout_text = stdout_match.group(1).strip()
                        if stdout_text:
                            out.write(f"  \u23bf  {stdout_text}\n")
                        continue

                    if "continued from a previous conversation" in text:
                        out.write(f"\n\u276f {text[:200]}\n")
                        if len(text) > 200:
                            for tl in text[200:].splitlines():
                                out.write(f"{truncate_line(tl)}\n")
                        continue

                    lines = text.splitlines()
                    out.write(f"\n\u276f {lines[0]}\n")
                    for ul in lines[1:]:
                        out.write(f"{ul}\n")
                    continue

                elif isinstance(content, list):
                    for block in content:
                        btype = block.get("type", "")

                        if btype == "tool_result":
                            is_error = block.get("is_error", False)
                            result_content = block.get("content", "")
                            if is_error:
                                err_text = str(result_content)
                                out.write(f"  \u23bf  Error: {truncate_line(err_text)}\n")
                            else:
                                result_lines = format_tool_result_content(result_content)
                                for rl in result_lines:
                                    out.write(f"  \u23bf  {rl}\n")
                            out.write("\n")
                            continue

                        if btype == "text":
                            text = block.get("text", "").strip()
                            if "[Request interrupted by user]" in text:
                                out.write(f"\n\u276f {text}\n")
                            elif text:
                                lines = text.splitlines()
                                out.write(f"\n\u276f {lines[0]}\n")
                                for ul in lines[1:]:
                                    out.write(f"{ul}\n")
                            continue

            if rec_type == "assistant" and role == "assistant":
                if isinstance(content, list):
                    for block in content:
                        btype = block.get("type", "")

                        if btype == "thinking":
                            thinking_text = block.get("thinking", "")
                            if thinking_text:
                                preview = thinking_text[:MAX_THINKING_CHARS].replace("\n", " ")
                                if len(thinking_text) > MAX_THINKING_CHARS:
                                    preview += "..."
                                out.write(f"\n  [thinking] {preview}\n")

                        elif btype == "text":
                            text = block.get("text", "").strip()
                            if text:
                                wrapped = wrap_text_block(text, "\u23fa ", "  ")
                                out.write(f"\n{wrapped}\n")

                        elif btype == "tool_use":
                            tool_id = block.get("id", "")
                            raw_name = block.get("name", "???")
                            inp = block.get("input", {})
                            display_name = format_tool_name(raw_name)
                            summary = summarise_tool_input(raw_name, inp)
                            tool_uses[tool_id] = display_name
                            out.write(f"\n\u23fa {display_name}({summary})\n")
                            if raw_name == "Bash" and inp.get("description"):
                                out.write(f"  # {inp['description']}\n")

                elif isinstance(content, str) and content.strip():
                    wrapped = wrap_text_block(content.strip(), "\u23fa ", "  ")
                    out.write(f"\n{wrapped}\n")

            if rec_type == "system" and record.get("subtype") != "api_error":
                if isinstance(content, str) and content.strip():
                    out.write(f"\n  [system] {truncate_line(content.strip())}\n")


# ---------------------------------------------------------------------------
# MD format — assistant text renders natively, tools in fenced code blocks
# ---------------------------------------------------------------------------

def convert_md(input_path: str, out):
    session_id = os.path.basename(input_path).removesuffix(".jsonl")
    banner_printed = False

    out.write(f"<!-- claude --resume {session_id} -->\n")

    # Load all records upfront so we can lookahead
    records = []
    with open(input_path) as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                records.append(json.loads(raw_line))
            except json.JSONDecodeError:
                continue

    def next_unskipped(i):
        """Return the next record after index i that won't be skipped, or None."""
        for j in range(i + 1, len(records)):
            if not should_skip(records[j]):
                return records[j]
        return None

    for i, record in enumerate(records):
            if should_skip(record):
                continue

            rec_type = record.get("type", "")
            msg = record.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content", "")

            # --- Session banner -----------------------------------------------
            if not banner_printed and rec_type == "user" and record.get("version"):
                version = record.get("version", "")
                cwd = record.get("cwd", "")
                out.write(f"\n> Claude Code v{version} · `{cwd}`\n\n")
                banner_printed = True

            # --- User messages -----------------------------------------------
            if rec_type == "user" and role == "user":
                nxt = next_unskipped(i)
                next_is_assistant = (
                    nxt is not None
                    and nxt.get("type") == "assistant"
                    and nxt.get("message", {}).get("role") == "assistant"
                )
                claude_suffix = "\n\n---\n\n**Claude**" if next_is_assistant else ""

                if isinstance(content, str):
                    text = content.strip()
                    if not text:
                        continue

                    cmd_match = re.search(r"<command-name>(.*?)</command-name>", text)
                    if cmd_match:
                        cmd = cmd_match.group(1)
                        if not cmd.startswith("/"):
                            cmd = "/" + cmd
                        args_match = re.search(r"<command-args>(.*?)</command-args>", text, re.DOTALL)
                        args = args_match.group(1).strip() if args_match else ""
                        line = f"{cmd} {args}".rstrip()
                        out.write(f"\n---\n\n**❯ User**\n\n`{line}`{claude_suffix}\n")
                        continue

                    stdout_match = re.search(
                        r"<local-command-stdout>(.*?)</local-command-stdout>", text, re.DOTALL
                    )
                    if stdout_match:
                        stdout_text = stdout_match.group(1).strip()
                        if stdout_text:
                            out.write(f"\n```\n{stdout_text}\n```\n")
                        continue

                    if "continued from a previous conversation" in text:
                        out.write(f"\n---\n\n**❯ User**\n\n_{text[:200]}_{claude_suffix}\n")
                        continue

                    out.write(f"\n---\n\n**❯ User**\n\n{text}{claude_suffix}\n")
                    continue

                elif isinstance(content, list):
                    for block in content:
                        btype = block.get("type", "")

                        if btype == "tool_result":
                            is_error = block.get("is_error", False)
                            result_content = block.get("content", "")
                            result_lines = format_tool_result_content(result_content)
                            result_text = "\n".join(result_lines)
                            if is_error:
                                out.write(f"\n```\nError: {result_text}\n```\n")
                            else:
                                out.write(f"\n```\n{result_text}\n```\n")
                            continue

                        if btype == "text":
                            text = block.get("text", "").strip()
                            if text:
                                out.write(f"\n---\n\n**❯ User**\n\n{text}{claude_suffix}\n")
                            continue

            # --- Assistant messages ------------------------------------------
            if rec_type == "assistant" and role == "assistant":
                if isinstance(content, list):
                    for block in content:
                        btype = block.get("type", "")

                        if btype == "thinking":
                            thinking_text = block.get("thinking", "")
                            if thinking_text:
                                preview = thinking_text[:MAX_THINKING_CHARS].replace("\n", " ")
                                if len(thinking_text) > MAX_THINKING_CHARS:
                                    preview += "..."
                                out.write(f"\n> *[thinking] {preview}*\n")

                        elif btype == "text":
                            text = block.get("text", "").strip()
                            if text:
                                out.write(f"\n{text}\n")

                        elif btype == "tool_use":
                            raw_name = block.get("name", "???")
                            inp = block.get("input", {})
                            display_name = format_tool_name(raw_name)
                            summary = summarise_tool_input(raw_name, inp)
                            desc = inp.get("description", "") if raw_name == "Bash" else ""
                            if desc:
                                out.write(f"\n**`{display_name}({summary})`** — {desc}\n")
                            else:
                                out.write(f"\n**`{display_name}({summary})`**\n")

                elif isinstance(content, str) and content.strip():
                    out.write(f"\n{content.strip()}\n")

            # --- System messages ---------------------------------------------
            if rec_type == "system" and record.get("subtype") != "api_error":
                if isinstance(content, str) and content.strip():
                    out.write(f"\n> *[system] {truncate_line(content.strip())}*\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]

    # Pull out --format flag if present
    fmt = None
    filtered = []
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            filtered.append(args[i])
            i += 1
    args = filtered

    input_path = args[0]
    output_path = args[1] if len(args) >= 2 else None

    # Infer format from extension if not explicitly set; default is md
    if fmt is None:
        if output_path and output_path.endswith(".txt"):
            fmt = "txt"
        else:
            fmt = "md"

    converter = convert_md if fmt == "md" else convert_txt

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w") as f:
            converter(input_path, f)
        print(f"Wrote {fmt} transcript to {output_path}", file=sys.stderr)
    else:
        converter(input_path, sys.stdout)


if __name__ == "__main__":
    main()
