---
name: generate-pr-description
description: Use when generating a PR description for a feature branch.
---

# Generate PR Description

## Overview

Analyze a feature branch and produce a clear, neutral, reviewer-friendly PR description with a structured title and body.

## Step 0 — Resolve branch

Inspect `$ARGUMENTS`:

- If a GitHub tree URL is provided (e.g., `https://github.com/my-org/my-repo/tree/my-branch`), extract the branch name from the final path segment and the repo from the URL.
- If a bare branch name is provided, use it as BRANCH.
- If no arguments are provided, use the current branch: run `git rev-parse --abbrev-ref HEAD` and store as BRANCH. If this fails (e.g., detached HEAD), report the error and halt.

Run `git fetch origin BRANCH` to ensure the ref is current. If this fails (e.g., the branch doesn't exist on `origin`, or there is no network access), report the error and halt; do not fall back to a stale or local-only ref. Then run all subsequent commands against `origin/BRANCH` rather than `HEAD`.

## Step 0.5 — Resolve configuration

Read the following files in order using the Read tool (skip any that don't exist). For each key below, the last file that defines it wins. Do not use `echo` or any Bash command — env vars are not reliably injected into skill context.

1. `~/.claude/settings.json` (user-level) `env` object
2. For each directory from the filesystem root down to CWD (outermost first, CWD last — e.g., for CWD `~/repos/acme/widget-api` that's `~/repos`, `~/repos/acme`, `~/repos/acme/widget-api`), read `<dir>/.claude/settings.json` `env` object. This picks up a config set on a parent folder that contains multiple repos (e.g., an org-level `.claude/settings.json` shared by several nested client repos) as well as one set directly on the current repo.
3. For the same directories in the same order, read `<dir>/.claude/settings.local.json` `env` object.

Stop walking upward at the user's home directory (`~`) — do not read `.claude/settings.json` above it.

Keys:

- `BASE_TICKET_URL` — base URL for the issue tracker—e.g., `https://linear.app/acme/issue/` or `https://my-jira-instance.atlassian.net/browse/`. A ticket link is built as `{BASE_TICKET_URL}{TICKET-ID}`. If unset: if `$ARGUMENTS` includes a full ticket URL (a URL whose final path segment is a ticket ID—e.g., `[A-Z]+-\d+`), derive `BASE_TICKET_URL` by stripping that trailing ticket ID (keep the trailing slash). Otherwise omit the ticket link line from the output entirely (still reference the ticket ID in the summary/title if one was found).
- `TICKET_LABEL` — display label for the ticket link line—e.g., `Jira`, `Linear`, `Shortcut`. If unset, derive it from `BASE_TICKET_URL`'s hostname (whichever way `BASE_TICKET_URL` was resolved — configured or derived above):

  | Hostname contains | Label |
  | --- | --- |
  | `atlassian.net` | `Jira` |
  | `linear.app` | `Linear` |
  | `shortcut.com` | `Shortcut` |
  | `github.com` | `GitHub` |
  | anything else | title-cased first hostname segment—e.g., `tracker.example.com` → `Tracker` |

  If `BASE_TICKET_URL` is also unset (no ticket link at all), `TICKET_LABEL` is unused.
- `PR_DESC_OUTPUT_DIR` — directory to write the description file to. If unset, use `pwd`. Setting this alone (with `PR_DESC_DEFAULT_OUTPUT` unset) is enough to default to file output.
- `PR_DESC_DEFAULT_OUTPUT` — `file` or `chat`. If neither this nor `PR_DESC_OUTPUT_DIR` is set, defaults to `chat` (see Output routing).

```json
{
  "env": {
    "BASE_TICKET_URL": "https://linear.app/acme/issue/",
    "TICKET_LABEL": "Linear",
    "PR_DESC_OUTPUT_DIR": "~/ai-context/pr-descriptions",
    "PR_DESC_DEFAULT_OUTPUT": "file"
  }
}
```

## Required input artifacts

- Diff: run `git diff main origin/BRANCH`. If this fails (e.g., `main` doesn't exist locally), report the error and halt.
- Commit log: run `git log main..origin/BRANCH` (full messages — commit body often contains context). If this fails, report the error and halt.
- Issue/ticket: if a ticket number is referenced in the branch name or provided as an argument, fetch its content from the issue tracker. STOP gate: if a ticket ID was found but the fetch fails (e.g., no access, tracker unreachable), do not draft the description yet. Ask the operator whether to proceed without ticket context or resolve access first, and wait for their response before continuing. Writing the description first and only afterward flagging the missing context wastes their time.

STOP gate: if `origin/BRANCH` has no commits ahead of `main`, report "No commits ahead of main on branch BRANCH." and halt.

## PR title format

If a local skill config is present (see README), follow the title format rules defined there.

Otherwise, use Conventional Commits format:

```
<type>: <Imperative summary>
```

Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

- Imperative mood: "Add", "Enable", "Refactor"
- Neutral tone: prefer "update" / "revise" over "enhance" / "improve"
- No trailing punctuation; keep under ~80 characters

## Output structure

```md
# <PR title>

{TICKET_LABEL}: [TICKET-###: <ticket title>]({BASE_TICKET_URL}TICKET-###)

## Summary

2–4 sentences describing what this PR changes and what functionality or behavior it affects.

## Context

Optional: WHY these changes were made, citing the original issue or goals. If this is just a repetition of the summary, omit this section.

## Detailed changes

- Important code or structural updates
- Modules or major files modified
- Notable test or documentation additions
- Refactors (e.g., "Refactored X for dependency simplification")

## Testing

Optional. Include only to record verification that has already happened
and that will not be automatically run as a check in CI:

- Tests or checks that were actually run, and their result (e.g., "Ran the full suite locally: passing", "Manually verified the retry path against a local server")

Do not use this section to assign or remind about testing that still needs to happen; see "Surfacing to-dos and security issues" below.

## Breaking changes / migration steps

Any breaking changes or follow-up steps developers must perform.
If none: "None".

## Notes for reviewers

Optional. Include only if at least one applies:

- A known limitation or deliberate tradeoff isn't captured elsewhere
- There's a real open question for the reviewer to answer

If none apply, omit the section entirely. Do not restate the diff or
summary, and do not invent a testing step or caveat just to fill the
section. Do not use this section for testing status, to-dos, or security
concerns; see "Surfacing to-dos and security issues" below.
```

❌ WRONG:
```md
## Summary

This PR significantly improves the reliability of our payment retry logic
with a cleaner, more robust implementation.

## Notes for reviewers

Please review carefully.
```
(Appraises the code — "improves", "cleaner", "robust" — instead of describing what changed; "Notes for reviewers" restates nothing and gives the reviewer no useful information, so it should be omitted.)

❌ WRONG:
```md
## Notes for reviewers

The retry logic hasn't been tested against a real payment gateway yet, and
there's a possible timing issue with how we validate the webhook signature
that's worth a closer look.
```
(Buries an unperformed test and a possible security concern inside "Notes for
reviewers" instead of raising them to the operator in chat first; see
"Surfacing to-dos and security issues".)

If no ticket was found, or `BASE_TICKET_URL` is unset, omit the ticket link line entirely rather than printing a broken link.

If a local skill config is present, follow any output structure additions or modifications defined there.

## Surfacing to-dos and security issues

STOP gate: if, while drafting this description, you identify a to-do (a
manual test that still needs to be run, a flag that needs flipping, a
follow-up task) or a potential security issue, pause before composing or
routing the final output. Raise it directly to the operator in the chat
response—describe what you found and ask how they want it handled (e.g.,
run the test now, open a follow-up ticket)—and wait for their response
before finalizing the description. Do not write it into the PR description
itself, including "Notes for reviewers" or "Testing", as a caveat for
someone to notice later; that leaves the follow-through to whoever reads
the document instead of the person you're talking to right now, and a
reviewer's job is to review, not to pick up to-dos. Once the operator
responds, write only the outcome of that conversation into the artifact: a
manual test they said to run and that you or they then ran belongs in
"Testing"; if they want a to-do tracked, that becomes a follow-up ticket
(create one, or ask them to) referenced by its ticket number in the
description—never a task assigned to the PR reviewer.

## Style and tone

- Write **factually** and **concisely**
- Plain verbs: _add_, _update_, _replace_, _refactor_, _remove_, _enable_, _revise_
- **Avoid:** "enhance", "improve", "proper", "better", "optimized"
- Describe **what** and **why**; never appraise code quality
- Exclude changes that don't affect reviewer understanding: pure file/import reordering with no logic change, lockfile updates from a routine `npm install`/`go mod tidy`, and formatting-only diffs from an autoformatter run. Include a lockfile change only when it reflects a deliberate dependency version bump relevant to the PR's purpose.

## Output routing

Bind `OUTPUT` using the first matching rule below:

1. **Explicit arg**: If `$ARGUMENTS` includes a token matching `file:<path>` or a path ending in `.md`, set `OUTPUT = file:<path>`.
2. **Env default — file**: If `PR_DESC_DEFAULT_OUTPUT = file`, **or** `PR_DESC_DEFAULT_OUTPUT` is unset but `PR_DESC_OUTPUT_DIR` is set (setting a directory implies file output), set `OUTPUT = file:<PR_DESC_OUTPUT_DIR>/<BRANCH_SLUG>-pr-description.md`, where `BRANCH_SLUG` is `BRANCH` with every `/` replaced by `-` (so slashes in the branch name don't create subdirectories).
3. **No config set**: Neither `PR_DESC_DEFAULT_OUTPUT` nor `PR_DESC_OUTPUT_DIR` is set, or `PR_DESC_DEFAULT_OUTPUT = chat`. Set `OUTPUT = chat`.

If `OUTPUT = file:<path>` and a file already exists at that path, ask whether to overwrite it or use a different path before writing.

Route the finished description: `OUTPUT = chat` prints it in the response; `OUTPUT = file:<path>` writes it to that file (creating parent directories as needed) instead of printing the full body in chat — confirm the path written in a short chat message.

## Output Checklist

Before finalizing:

- [ ] Title is imperative, concise, no trailing punctuation
- [ ] All required sections are present: ticket link (if applicable), Summary, Detailed changes, Breaking changes
- [ ] Tone is neutral, factual, and reviewer-focused
- [ ] Notes for reviewers omitted unless a genuine trigger applies (not restating other sections)
- [ ] No to-dos or security issues buried in Testing/Notes for reviewers — raised to the operator in chat instead
- [ ] Fully explains what changed and why, without boastfulness or implied blame on previous work
- [ ] Output routed per `OUTPUT` (chat vs. file) resolved in Output routing
