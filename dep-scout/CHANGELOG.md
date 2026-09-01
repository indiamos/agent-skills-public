# Changelog

## 2026-07-23

- Replaced company-specific example values with generic placeholders

## 2026-07-09

- Parallel launch directive strengthened with explicit CRITICAL block and verbatim wording
- Bash tool prohibited in per-package agents; local file search switched from Bash `grep` to the `Grep` tool
- `TaskUpdate` call added after all per-package agents return

## 2026-07-07

- CI and scanner status lines use placeholder variables rather than hardcoded checkmarks, so unresolved values are visible
- Report header changed from `##` to `#`; package section headers changed from `###` to `##`; "Recommendation" section hoisted above package details
- Output defaults to file when `DEP_SCOUT_OUTPUT_DIR` is configured; file-overwrite confirmation prompt added
- PR header added to output (title and author)
- Initial release
