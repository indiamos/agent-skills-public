---
name: mine-pr-conventions
description: Use when you want to discover coding conventions, recurring mistakes, and design patterns from a GitHub repo's PR review history — to update CLAUDE.md, a spec-kit constitution, or a PR review checklist. Accepts any GitHub owner/repo and PR range.
---

# Mine PR Conventions

## Overview

Dispatch parallel subagents over batches of PRs. Each agent does first-pass synthesis. You route findings to the right documentation files after reviewing what's already there.

## Step 0 — Bind inputs before any other action

### 0★. GitHub MCP availability check

Before making any `gh` CLI calls or spawning any subagents, verify that the GitHub MCP server is installed, enabled, and authenticated by attempting to call its `get_authenticated_user` tool (or the closest equivalent available).

- If the call **succeeds**: GitHub MCP is available and authenticated. Proceed to argument binding below.
- If the call **fails with "tool not found", "unknown tool", or similar**: GitHub MCP is not installed or not enabled in this session.
- If the call **fails with an authentication or permission error**: GitHub MCP is installed but not authenticated.

**STOP gate:** If the MCP call failed for any reason, report the specific failure mode (not installed / not enabled / not authenticated) and ask:

> ⚠️ GitHub MCP is [not installed / not enabled / not authenticated]. Without it, this skill issues one `gh` CLI call per PR in the requested range — potentially hundreds — each of which may require an SSH fingerprint prompt on your machine.
>
> Proceed anyway? (yes / no)

Wait for the user's response. If **no**, halt immediately. If **yes**, continue.

Read the arguments provided when the skill was invoked.

- **owner/repo** — GitHub repository (e.g., `my-github-org/advisor`)
- **PR range** — start and end PR number (e.g., 400–538)
- **target files** — which docs to update (e.g., CLAUDE.md, constitution.md, PR-AGENT.md)

**STOP gate:** If owner/repo or PR range is missing, ask the user to provide them before continuing. Do not dispatch any subagents until both are bound.

If target files were not provided, ask: "Which documentation files should I route findings to?" and wait for a response.

Carry `OWNER_REPO`, `PR_START`, `PR_END`, and `TARGET_FILES` through all remaining steps.

---

## Step 1 — Dispatch subagents

**State check:** `OWNER_REPO`, `PR_START`, `PR_END`, and `TARGET_FILES` are bound.

Divide the range `PR_START`–`PR_END` into batches of 50. Launch one subagent per batch in parallel.

Use this prompt for each batch, substituting `START`, `END`, `OWNER`, `REPO`, and `TARGET_DOCS`:

```
For each PR numbered START through END in OWNER/REPO:

1. Fetch reviews, review comments, and issue comments using pull_request_read.
2. Skip PRs that match any of the following:
   - Approvals with no comment body
   - Comments consisting solely of: "LGTM", "looks good", "nice work", "ship it",
     ":+1:", "👍", or equivalent single-word/emoji praise
   - PRs opened by dependabot (author login starts with "dependabot")
   - Draft PRs with zero review events and zero inline comments
   Do not skip a PR because it "seems" low-signal — apply only these four criteria.
3. For PRs with real discussion, write one sentence capturing the key point of
   each comment thread.

Then identify recurring themes across the entire batch. Look specifically for:

- Mistakes reviewers caught (missing tests, wrong naming, unsafe queries, config gaps)
- Design decisions debated more than once (validation location, soft vs. hard delete,
  error log levels)
- Conventions cited by reviewers (naming patterns, SQL style, test structure)
- Workflow gaps (forgetting to run code generation, missing env var locations)

If no PRs in this range have substantive human review discussion, return:
"No findings: all PRs in this range had no human review discussion (unreviewed,
praise-only, or dependabot)."

Otherwise, return a structured findings list. Use this exact format for each
finding:

[THEME] Brief name (1 line)
[PRs] Comma-separated PR numbers where this appeared
[QUOTE] One representative reviewer comment verbatim (or "implicit" if the
        pattern was enforced without an explicit quote)
[SIGNAL] High or Medium — use this rubric:
  High:   Appeared in 2+ PRs AND specific enough to write as a rule
  Medium: Appeared once but an explicit team preference was stated, OR
          recurring but requires interpretation to make into a rule
[REASON] One sentence: what mistake this prevents or what convention it enforces

Skip findings with no identifiable pattern and no representative quote.
Skip Low-signal findings (one-off observations that don't represent a team
convention and aren't specific enough to write as a rule).

✅ CORRECT:
[THEME] Validation belongs in Validate() method, not service layer
[PRs] 524
[QUOTE] "It looks like there's an existing Validate() method... Would it make
        sense to add this validation there instead, for consistency?"
[SIGNAL] Medium — appeared once but explicit team preference stated
[REASON] Prevents validation logic from scattering across service methods when
         a canonical location already exists on the struct.

❌ WRONG:
[THEME] Code quality
[PRs] multiple
[QUOTE] various
[SIGNAL] High
[REASON] There were several code quality issues.
(Too vague — no specific pattern, no actionable rule)

We'll use these findings to update: TARGET_DOCS.
```

---

## Step 2 — Synthesize

**State check:** All subagents have returned.

**STOP gate:** If all subagents returned "No findings", report that the range had no human review discussion to analyze and halt.

1. **Merge findings** across batches, collapsing duplicates. Combine PR numbers for findings that appeared in multiple batches.

2. **Read all candidate target files** — including `TARGET_FILES`, `.claude/rules/*.md`, and `.claude/skills/*/SKILL.md` — so you know what's already covered.

   For each path in `TARGET_FILES`: if the file does not exist, report which path failed and ask the user whether to create it during the write step or provide a different path. Do not halt for missing `.claude/rules/` or `.claude/skills/` files — treat them as empty if absent. Only halt if every path in `TARGET_FILES` is unreadable.

3. **Annotate and present each finding** using this exact format:

   ```
   [NEW] or [ALREADY COVERED: <file, section>]
   [THEME] <from subagent output>
   [PRs] <from subagent output>
   [SIGNAL] High or Medium
   [DESTINATION] <target file and section> (for [NEW] findings only)
   [PROPOSED TEXT] <exact text to add, ready to copy> (for [NEW] findings only)
   ```

   ✅ CORRECT:

   ```
   [NEW]
   [THEME] Validation belongs in Validate() method, not service layer
   [PRs] 524
   [SIGNAL] Medium
   [DESTINATION] CLAUDE.md — Non-Obvious Conventions
   [PROPOSED TEXT] Add validation logic to the struct's Validate() method rather than
                   scattering it across service methods.
   ```

   ✅ CORRECT:

   ```
   [ALREADY COVERED: CLAUDE.md — DB engines]
   [THEME] Most Go services use MariaDB/MySQL
   [PRs] 512, 518
   [SIGNAL] High
   ```

   ❌ WRONG:

   ```
   [NEW]
   [THEME] Code quality
   [PROPOSED TEXT] Improve code quality practices.
   ```

   (Too vague — no actionable rule, no destination section)

   List all `[ALREADY COVERED]` findings first, then all `[NEW]` findings. `[ALREADY COVERED]` findings confirm the existing guidance is complete; `[NEW]` findings are candidates for addition.

4. **Route each `[NEW]` finding**:

   | Finding type                                                      | Where it belongs                                         |
   | ----------------------------------------------------------------- | -------------------------------------------------------- |
   | Architectural principle (DB layer, deletion strategy, SQL safety) | constitution.md                                          |
   | Dev workflow (always-applicable short rules)                      | CLAUDE.md                                                |
   | Convention scoped to a file type or directory                     | `.claude/rules/<topic>.md` (path-scoped, auto-activates) |
   | Task-specific procedural steps                                    | `.claude/skills/<task>/SKILL.md`                         |
   | Review checklist item (what to look for in a PR)                  | PR-AGENT.md                                              |
   | Multiple of the above                                             | All that apply                                           |

5. **For schema/migration findings**, verify against actual migration files before writing guidance. Review-comment descriptions of conventions may be imprecise; the migrations are the ground truth.

6. **Present the proposed changes for discussion** before writing anything:
   1. Print the full annotated findings list (both `[NEW]` and `[ALREADY COVERED]`) in the chat.
   2. For each `[NEW]` finding, show the proposed addition verbatim (exact text that would be inserted, with the target file and section identified).
   3. Ask: "Should I apply these additions? (yes / no / select)"
      - **yes** — write all proposed additions to their target files
      - **no** — halt; leave all files unchanged
      - **select** — number each proposed addition; wait for the user to specify which to apply by number, then apply only those
   4. Do not write to any file until the user responds.

   Writing to files and committing are separate steps after this confirmation.
