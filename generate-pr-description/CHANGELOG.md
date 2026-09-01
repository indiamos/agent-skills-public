# Changelog

## 2026-08-14

- Removed Jira assumption: ticket link now built from `BASE_TICKET_URL` / `TICKET_LABEL` env vars (settings.json cascade, same pattern as `pr-scout`'s `PR_SCOUT_OUTPUT_DIR`), so Linear, Shortcut, GitHub Issues, or any tracker works without a local override
- `BASE_TICKET_URL`, if unset, is derived by stripping the ticket ID from a full ticket URL passed as an argument
- `TICKET_LABEL`, if unset, is derived from `BASE_TICKET_URL`'s hostname (Jira/Linear/Shortcut/GitHub known hosts, else title-cased hostname segment)
- Added `PR_DESC_OUTPUT_DIR` / `PR_DESC_DEFAULT_OUTPUT` env vars and an `Output routing` step to write the description to a markdown file instead of only printing it in chat; `file:<path>` argument overrides per-invocation. Setting `PR_DESC_OUTPUT_DIR` alone (without `PR_DESC_DEFAULT_OUTPUT`) defaults to file output; setting neither defaults to chat (no prompt)

## 2026-08-12

- "Notes for reviewers" tightened to concrete inclusion triggers (non-obvious test step, known limitation/tradeoff, real open question) instead of a vague "if really needed" standard
- Output checklist now verifies the section is omitted unless a genuine trigger applies

## 2026-05-27

- Section headers normalized to sentence case
- "Why" section made optional — omit if it would just restate the summary
- Jira link format added to output template

## 2026-05-12

- Examples updated to use generic `XYZ-` ticket prefix instead of org-specific one

## 2026-05-06

- `--no-pager` flag removed from git commands

## 2026-04-15

- Step 0 added: branch resolved from arguments (GitHub URL, bare branch name, or current HEAD via `git rev-parse`); `git fetch origin` run before diff/log; all subsequent commands run against `origin/BRANCH` rather than `HEAD`
- Initial release
