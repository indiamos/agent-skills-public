# Changelog

## 2026-05-26

- Output dir resolution delegated entirely to the `find-current` Python subcommand

## 2026-05-22

- Project dir derivation now replaces underscores with hyphens in addition to slashes and dots

## 2026-05-12

- Output dir resolution updated to three-level settings cascade (user → project → project-local, last wins); env var injection via Bash no longer used

## 2026-05-05

- Finalize command now requires inline absolute paths instead of shell variables, preventing variable expansion failures in Bash calls

## 2026-05-01

- `find-current` subcommand switched from accepting `$PWD` as an argument to using `os.getcwd()` internally
- Session discovery fully delegated to `export-session.py find-current`, eliminating the complex `find | stat | sort | head` pipeline
- Permission prompts reduced by consolidating `find` and timestamp extraction into a single Bash call

## 2026-04-21

- Added `EXPORT_FULL_OUTPUT_DIR` env var for configuring output directory

## 2026-04-15

- Updated project folder derivation logic

## 2026-03-31

- Initial release
