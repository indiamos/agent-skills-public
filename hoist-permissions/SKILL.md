---
name: hoist-permissions
description: "Run the permissions hoister script and report the results. Use when: updating tool permissions, reviewing current permission settings, after adding new tool allowances."
---

Run the permissions hoister script and report the results.

Read `~/.claude/settings.json` using the Read tool. If its `env` object contains `HOIST_PERMISSIONS_SKIP`, pass the value as `--skip` to the script (serialize as JSON). Otherwise run the script with no `--skip` argument it will read `HOIST_PERMISSIONS_SKIP` from settings.json directly.

```bash
# With skip list:
python3 ~/.claude/skills/hoist-permissions/hoist-permissions.py --skip '<json-array>'

# Without skip list:
python3 ~/.claude/skills/hoist-permissions/hoist-permissions.py
```

Display the output clearly:

1. Show the path of the written file
2. List all settings files that contain values (from the "Settings files with content:" section of the output)
3. If there are parse errors in the output, surface them as a warning
4. If the script exits non-zero, report the error from stderr and stop

## Configuration

Set either or both env vars in `~/.claude/settings.json` under `env`:

- `HOIST_PERMISSIONS_ROOTS` — comma-separated root directories to scan. Defaults to `~/.claude,~/repos`.
- `HOIST_PERMISSIONS_SKIP` — comma-separated paths to exclude. Folder entries skip everything under them; file entries skip only that file. Defaults to no skips.

```json
{
  "env": {
    "HOIST_PERMISSIONS_ROOTS": "~/.claude,~/work/repos,~/personal/repos",
    "HOIST_PERMISSIONS_SKIP": "~/.claude/plugins/, ~/work/repos/some-project/.claude/settings.json"
  }
}
```

The `--roots` and `--skip` CLI flags override the env vars when passed explicitly.
