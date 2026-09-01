# Changelog

## 2026-07-24

Split org-specific conventions into a sibling rider file (`SKILL.<company>.md`). Base skill
checklist and reference are now client-agnostic; public sync excludes rider files.

## 2026-07-13

Initial release. Seven-category checklist derived from post-migration fix history across
several Go services after CircleCI→GHA migrations. Covers: missing CI workflows,
deployment gating, secret names, permissions, Helm deploy steps, Go CI patterns, and
Slack notification completeness.
