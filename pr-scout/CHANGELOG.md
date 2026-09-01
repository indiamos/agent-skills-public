# Changelog

## 2026-08-20

- Agent 2 (bug scan) now also checks for fail-open authorization/security guards (a
  missing config value, permission, or flag treated as "no restriction" instead of
  failing closed) and for auth changes that break a route's OPTIONS/preflight
  handling — both phrased generically, not tied to any one language or framework.
  Prompted by a human reviewer catching both on an Apigee PR that pr-scout had
  already reviewed twice without flagging either.

## 2026-07-10

- Report header now includes PR title, GitHub URL, and a horizontal rule before the issue count
- Collapsed verbose modification history in attribution comment to a single line

## 2026-06-17

- Added Step 4.5 hypothetical framing gate: parallel verification agents confirm or drop any issue phrased with conditional language ("could", "might", "possible") before it reaches the scorer
- Specialist agents now required to verify before using conditional language — hedging is a signal to check the code, not a reporting style
- Hypothetically-framed issues that were accessible to the specialist agent capped at score 25
- Step 4 parallel dispatch now specifies `model: "sonnet"`
- Appendix B pre-existing early-return exception rewritten as a conditional routing gate

## 2026-05-15

- Added `PR_SCOUT_DEFAULT_OUTPUT` env var (`file` or `github`) to skip the output-mode prompt; file-overwrite and GitHub-preview guards remain in place regardless
- Added Step 9: structural task-list cleanup pass that marks any remaining pending or in-progress tasks completed, self-healing cases where per-step completions were missed
- Per-step `TaskUpdate` calls added inline at every subagent handoff point so the model doesn't have to recall a global rule mid-execution

## 2026-05-12

- Revised org-specific examples to make the skill portable across organizations

## 2026-05-05

- Agents now required to verify an issue by reading the relevant code before flagging it — answers visible in the diff or file contents must be resolved, not surfaced as questions

## 2026-04-27

- Fixed `PR_SCOUT_OUTPUT_DIR` resolution to use a three-level cascade (user settings → project settings → project-local settings), with the last defined value winning

## 2026-04-24

- Step 0★ updated to use `get_me` (official GitHub MCP server); reviewer login extracted from the response, eliminating a redundant `gh api` call
- Output mode prompt replaced with `AskUserQuestion` tool
- Commit compliance check removed from the interactive prompt; `CHECK_COMMITS` now set by passing the `commits` token as a skill argument
- CLAUDE.md path discovery now falls back to the local `Read` tool when GitHub returns a 404
- Tasks now marked completed per step, not batched at the end
- MCP-first guidance replaces gh-first: `gh` CLI used only when an MCP call explicitly fails or has no MCP equivalent
- All tool names updated from `mcp__plugin_github_github__` to `mcp__github__`

## 2026-04-16

- Added `PR_SCOUT_OUTPUT_DIR` env var, configurable in `~/.claude/settings.json` or `.claude/settings.local.json`, to avoid manually editing the output path on every run
- Default output filename now uses the PR number only (e.g., `2026-04-16-1351-pr-576-review.md`), dropping the org/repo slug
- Added `PR-AGENT.md` support: Agent 1 now audits against a repo-level PR review criteria file if one exists

## 2026-04-15

- Clarified commit message subject line length rule

## 2026-04-01

- Specialist and scoring agents prohibited from using the Bash tool; MCP-first data access required
