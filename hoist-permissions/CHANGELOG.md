# Changelog

## 2026-08-31

- `HOIST_PERMISSIONS_ROOTS` env var added to configure which root directories are scanned (default: `~/.claude,~/repos`)

## 2026-05-22

- `HOIST_PERMISSIONS_SKIP` format changed from JSON array to comma-separated string
- `HOIST_PERMISSIONS_SKIP` env var added to exclude specific paths from the scan
- Script moved from `~/.claude/scripts/` into the skill directory

## 2026-03-31

- Initial release
