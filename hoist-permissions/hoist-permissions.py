#!/usr/bin/env python3
"""Aggregate Claude permission entries from project settings files."""

import argparse
import json
import os
import pathlib
import sys


DEFAULT_ROOTS = "~/.claude,~/repos"
USER_SETTINGS_PATH = pathlib.Path("~/.claude/settings.json").expanduser()
EXCLUDE = {
    USER_SETTINGS_PATH,
    pathlib.Path("~/.claude/settings-hoisted.json").expanduser(),
}
OUTPUT_PATH = pathlib.Path("~/.claude/settings-hoisted.json").expanduser()


def load_skip_list() -> list[str]:
    """Read HOIST_PERMISSIONS_SKIP from ~/.claude/settings.json env section."""
    if not USER_SETTINGS_PATH.exists():
        return []
    try:
        data = json.loads(USER_SETTINGS_PATH.read_text())
        value = data.get("env", {}).get("HOIST_PERMISSIONS_SKIP", "")
        if isinstance(value, str):
            return [p for p in (p.strip() for p in value.split(",")) if p]
    except Exception:
        pass
    return []


def should_skip(path: pathlib.Path, skip_paths: list[pathlib.Path]) -> bool:
    if not skip_paths:
        return False
    resolved = path.resolve()
    for skip in skip_paths:
        try:
            resolved.relative_to(skip)
            return True
        except ValueError:
            pass
    return False


def discover(roots: list[pathlib.Path], skip_paths: list[pathlib.Path] | None = None) -> list[pathlib.Path]:
    """Find all .claude/settings*.json files under the given roots, excluding EXCLUDE."""
    if skip_paths is None:
        skip_paths = []
    found = []
    for root in roots:
        for path in root.rglob(".claude/settings*.json"):
            if path.resolve() not in EXCLUDE and not should_skip(path, skip_paths):
                found.append(path)
    return found


def parse_file(path: pathlib.Path) -> tuple[dict | None, str | None]:
    """Parse a JSON file. Returns (data, None) on success, (None, error_msg) on failure."""
    try:
        data = json.loads(path.read_text())
        return data, None
    except Exception as e:
        return None, f"JSON parse error: {e}"


def _is_non_empty(value) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (str, list, dict)):
        return bool(value)
    return False


def has_content(data: dict) -> bool:
    """Return True if the parsed data has at least one non-empty field."""
    for value in data.values():
        # Booleans are always content
        if isinstance(value, bool):
            return True
        # Strings: non-empty strings are content
        if isinstance(value, str):
            if value:
                return True
            continue
        # Lists: non-empty lists are content
        if isinstance(value, list):
            if value:
                return True
            continue
        # Dicts: recursively check
        if isinstance(value, dict):
            if has_content(value):
                return True
    return False


def aggregate(parsed_files: list[dict]) -> tuple[list[str], list[str]]:
    """Collect, dedup (case-sensitive), and sort (case-insensitive) allow/deny entries."""
    allow_set: dict[str, None] = {}  # ordered dict as ordered set
    deny_set: dict[str, None] = {}

    for data in parsed_files:
        perms = data.get("permissions", {})
        for entry in perms.get("allow", []):
            allow_set[entry] = None
        for entry in perms.get("deny", []):
            deny_set[entry] = None

    allow = sorted(allow_set.keys(), key=str.casefold)
    deny = sorted(deny_set.keys(), key=str.casefold)
    return allow, deny


def write_hoisted(allow: list[str], deny: list[str], output_path: pathlib.Path) -> None:
    """Write aggregated permissions to output_path. Raises OSError on failure."""
    perms: dict = {}
    if allow:
        perms["allow"] = allow
    if deny:
        perms["deny"] = deny
    data = {"permissions": perms}

    # Write via a temp file to avoid partial writes
    tmp = output_path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2) + "\n")
        tmp.replace(output_path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--roots",
        default=os.environ.get("HOIST_PERMISSIONS_ROOTS", DEFAULT_ROOTS),
        help=f"Comma-separated list of directories to search (default: {DEFAULT_ROOTS}; overridden by HOIST_PERMISSIONS_ROOTS env var)",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help=f"Output file path (default: {OUTPUT_PATH})",
    )
    parser.add_argument(
        "--skip",
        default=None,
        help="JSON array of paths to skip (overrides HOIST_PERMISSIONS_SKIP in ~/.claude/settings.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    roots = [pathlib.Path(r.strip()).expanduser() for r in args.roots.split(",")]
    output_path = pathlib.Path(args.output).expanduser()

    # Resolve skip list: --skip overrides settings.json
    if args.skip is not None:
        try:
            raw_skip = json.loads(args.skip)
            if not isinstance(raw_skip, list):
                print("ERROR: --skip must be a JSON array", file=sys.stderr)
                sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"ERROR: --skip is not valid JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        raw_skip = load_skip_list()
    skip_paths = [pathlib.Path(s).expanduser().resolve() for s in raw_skip]

    # Step 1: Discover
    files = discover(roots, skip_paths)

    # Step 2–3: Parse and classify
    parsed_data = []
    files_with_content = []
    parse_errors = []

    for path in files:
        data, error = parse_file(path)
        if error:
            parse_errors.append((path, error))
            continue
        if has_content(data):
            files_with_content.append(path)
        parsed_data.append(data)

    # Step 4: Aggregate
    allow, deny = aggregate(parsed_data)

    # Step 5: Write
    try:
        write_hoisted(allow, deny, output_path)
    except OSError as e:
        print(f"ERROR: could not write {output_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 6: Report
    print(f"Written: {output_path.resolve()}")
    print()
    if files_with_content:
        print("Settings files with content:")
        for path in sorted(files_with_content, key=lambda p: str(p).casefold()):
            print(f"  {path.resolve()}")
    else:
        print("No settings files with content found.")
    if parse_errors:
        print()
        print("Parse errors:")
        for path, error in parse_errors:
            print(f"  {path.resolve()}: {error}")


if __name__ == "__main__":
    main()
