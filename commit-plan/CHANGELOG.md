# Changelog

## 2026-08-14

- Generalized ticket-number extraction wording from "Jira ticket number" to "ticket ID" (tracker-agnostic)

## 2026-05-12

- Examples updated to use generic `XYZ-` ticket prefix instead of org-specific one

## 2026-04-21

- Added `COMMIT_PLAN_OUTPUT_DIR` env var for configuring output directory

## 2026-04-15

- Git data gathering restructured: each command result stored as a named variable; explicit regex pattern for TICKET extraction; halts with a prompt if no ticket match found
- Improved guidance on which changes to skip (import reordering, lockfile updates)
- Initial release
