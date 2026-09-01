# Changelog

## 2026-09-01

- Working-tree survey now also checks the current branch name for a ticket reference (e.g., `XYZ-123`) and uses it by default in the Ticket References step, instead of only asking the user

## 2026-08-14

- Ticket reference wording generalized from "Jira ticket" to "tracked ticket (Jira, Linear, Shortcut, etc.)"

## 2026-05-12

- Examples updated to use generic `XYZ-` ticket prefix instead of org-specific one

## 2026-05-05

- Renamed from `commit-messages` to `commit-message`
- Subject-line length verification now requires running `printf '%s' '...' | wc -c` — mental counting explicitly prohibited
- Git status and diff commands now dispatched as a parallel tool-call batch
- Error handling added if git is unavailable or the directory is not a repo
- Verified length shown as literal command output in responses so the user can audit it

## 2026-03-31

- Initial release
