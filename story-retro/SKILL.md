---
name: story-retro
description: "Retrospective analysis of completed tracked tickets (Jira, Linear, ...). Use when a developer or team lead wants to learn from completed work by comparing original ticket scope to final implementation."
argument-hint: "query-or-ticket-id [output-dir]"
---

# Story Retro

Analyzes completed tickets against their associated PRs to produce a coaching-oriented retrospective. Helps developers see concretely how their tickets could have prevented rework, extended review cycles, and late requirement discovery.

## Step 0 — Bind state variables

### 0★. Tracker availability

Check which tracker MCP is present in the current tool list:

- Is a Jira/Atlassian MCP tool present (e.g. any `mcp__*jira*__*` or `mcp__*atlassian*__*`)?
- Is a Linear MCP tool present (e.g. any `mcp__*linear*__get_issue`)?

Exactly one should be present in a normal session (each client engagement uses one tracker).
Store the result as **TRACKER** (`jira` or `linear`). If both or neither are present, ask the
user which tracker to use. Store its display name as **TRACKER_LABEL** (`Jira` / `Linear`).

Read `trackers/{TRACKER}.md` now (e.g. `trackers/jira.md`) — every later step marked "see
tracker file" refers to the matching section there.

### 0†. GitHub MCP availability check

Before making any `gh` CLI calls or spawning any subagents, verify that the GitHub MCP server is installed, enabled, and authenticated by attempting to call its `get_authenticated_user` tool (or the closest equivalent available).

- If the call **succeeds**: GitHub MCP is available and authenticated. Proceed to argument binding below.
- If the call **fails with "tool not found", "unknown tool", or similar**: GitHub MCP is not installed or not enabled in this session.
- If the call **fails with an authentication or permission error**: GitHub MCP is installed but not authenticated.

**STOP gate:** If the MCP call failed for any reason, report the specific failure mode (not installed / not enabled / not authenticated) and ask:

> ⚠️ GitHub MCP is [not installed / not enabled / not authenticated]. Without it, this skill issues hundreds of `gh` CLI calls — each of which may require an SSH fingerprint prompt on your machine.
>
> Proceed anyway? (yes / no)

Wait for the user's response. If **no**, halt immediately. If **yes**, continue.

- **GITHUB_ORG**: Infer from `git remote get-url origin` by extracting the org segment (e.g., `git@github.com:my-github-org/repo.git` → `my-github-org`). If no git remote is found or the remote URL is ambiguous, ask the user.

Read the arguments provided when the skill was invoked.

- **INPUT**: The argument may be any of the following — accept all of them:
  - A single ticket ID: `XYZ-1038`
  - A comma-separated list: `XYZ-1038, XYZ-1042`
  - A range expressed in natural language: "XYZ-885 and higher", "all XYZ tickets since 2025-11-13", "my tickets from last sprint", etc.
  - A raw native query string in the active tracker's query language (e.g. JQL for Jira) — pass through as-is
- **OUTPUT_DIR**: The last token that looks like a file path or directory, if present in the arguments. If not, leave it unset for now — you will ask after the query is confirmed.

**Translate INPUT to the active tracker's native query**, following `trackers/{TRACKER}.md`'s
"Build the query" section, then present it to the user for approval before proceeding:

```
I'll use this query:

  <derived query>

Proceed? (yes / edit)
- yes — continue with this query
- edit — paste your corrected query and I'll use that instead
```

Wait for the user's response before continuing. Store the confirmed query as **TICKET_QUERY**.

If OUTPUT_DIR was not provided in the arguments, now ask:
Compute the current date and time and format it as `YYYY-MM-DD-HHMM` (e.g., `2026-03-18-1430`). Then ask:

> "Where should I write the output? (default: `~/retro-YYYY-MM-DD-HHMM/`)"
> substituting the actual computed timestamp. Wait for the response. If the user confirms the default or presses enter without typing, use that path. Otherwise use the path they provide. Store the result as **OUTPUT_DIR**.

Announce: "Running story retro. Output will be written to `<OUTPUT_DIR>`."

Create the output directory if it does not exist.
If directory creation fails (e.g., permission denied, invalid path), report
the error and halt — all subsequent writes depend on this directory existing.

## Step 1 — Fetch ticket list

Fetch the list of tickets matching **TICKET_QUERY** — see `trackers/{TRACKER}.md`'s "Fetch the
ticket list" section for the exact call, pagination limits, and lightweight-fields guidance
(request only what's needed to build the dispatch list; full ticket data is fetched per-ticket
by each subagent in Step 3).

If the call returns an error or zero results due to a query failure
(not because no tickets matched), report the error and halt — distinguish
"no matching tickets" (proceed to Step 2) from "fetch failed" (halt).

Skip tickets that aren't in a completed/done state. Note each skipped ticket ID and its
current status in the aggregate summary.

Also fetch one recently-completed **bug ticket** from the project (lightweight, just title + description) to use as a structural reference in Step 6. Note whether it has explicit sections like Background, Steps to Reproduce, Acceptance Criteria, etc. Trackers generally don't expose templates directly — inferring from recent tickets is the correct approach.

## Step 2 — Dispatch one subagent per ticket (parallel)

1. Count the tickets returned in Step 1. Call this N.
2. Announce: "Found N tickets. Processing all N."
3. If N = 0: stop and report "No Done tickets matched the scope."
4. If N = 1: execute Steps 3–7 inline (no subagent needed). Skip to Step 8 when done.
5. If N > 1:

   <use_parallel_tool_calls>
   Launch all N `general-purpose` Task tool calls in a single message simultaneously:

   | Agent          | Input                 | Task                                                           |
   | -------------- | --------------------- | -------------------------------------------------------------- |
   | One per ticket | Ticket ID, OUTPUT_DIR | Follow Steps 3–7 and return the structured summary from Step 7 |

   Each agent must:
   - Return a fully-formed file path for the report it wrote
     (absolute path, not a relative reference) — so the parent can
     verify file creation without a follow-up fetch.
   - Fetch all ticket data itself using separate, targeted API calls (see Step 3a).

   Wait for all agents to return before proceeding to Step 8.

6. Collect results:
   - If ALL subagents failed: report "All N ticket agents failed — no reports
     written." and halt.
   - If SOME subagents failed: report which ticket IDs failed and why, then
     proceed to Step 8 using results from successful agents only.
   - If ALL succeeded: proceed to Step 8.

**Do not remove any ticket from the list before dispatching.** The dispatch count must equal N from step 1. Whether a ticket has code changes, PRs, or meaningful AC is determined in Step 3 — not here.

---

## Per-ticket subagent instructions (Steps 3–7)

### Step 3a — Fetch ticket data

See `trackers/{TRACKER}.md`'s "Fetch full ticket data" section for the exact call(s) and any
size-fallback handling.

### Step 3b — Find associated PRs

1. **Search method A — native tracker link**: see `trackers/{TRACKER}.md`'s "Find linked PRs"
   section for how this tracker surfaces PRs it already knows about (e.g. Jira's development
   panel, Linear's issue attachments). Record count: A.
2. **Search method B — GitHub title/branch search**: search `org:<GITHUB_ORG>` for the ticket ID (e.g., `XYZ-1038`) in PR titles and branch names across all repos. Record count: B.
3. **Search method C — GitHub body search**: search `org:<GITHUB_ORG>` for the ticket ID and the ticket's URL in PR body text across all repos. Record count: C.
4. Take the union of A + B + C. Deduplicate by PR URL. Record which method(s) found each PR.
5. Announce: "Found [total] PRs for [TICKET-ID]: [A] via native tracker link, [B] via title/branch search, [C] via body search ([X] deduplicated)."
6. If total = 0: mark ticket as **`<TRACKER_LABEL>`-only**. Skip Steps 4–5; proceed to Step 6 with reduced analysis.
7. If total > 0: assign confidence label and traceability flag:
   - **Confidence**: `Full` if any PR found via the native tracker link; `Partial` if only GitHub search; `<TRACKER_LABEL>-only` if none.
   - **PR traceability**: `Linked proactively ✓` if the native-link count > 0; `Found only via text search ✗` otherwise.
8. For each PR in the union, fetch: PR description, all review comments (inline and top-level), PR timeline (opened, first review, merge), reviewer names (note external code owners).

### Step 4 — Analyze timeline

Compute three cycle time figures:

| Metric                  | How to compute                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------ |
| **Implementation time** | First commit timestamp → last PR merged                                              |
| **Total elapsed**       | First of: (ticket moved to `In Progress`) or (first commit) → ticket moved to `Done` |
| **Review rounds**       | Count distinct periods of "PR open, no merge, reviewer comments added"               |

Note: A gap between PR open and first reviewer comment does not reliably
indicate slow reviewer response — the PR may not have been requested for
review yet. Reporting it as a review wait issue without verification would
produce a misleading finding.

For each review round:

1. Compute the gap between (a) the last comment posted by the PR author
   on their own PR before any reviewer activity — or PR open time if the
   author posted no self-comments — and (b) the first reviewer comment in
   that round.
2. If the gap is < 3 calendar days: record it as-is; no Slack lookup needed.
3. If the gap is ≥ 3 calendar days: search Slack for the PR URL to find
   when it was first shared or review was requested.
   - If found: note both the Slack share time and the GitHub gap; compute
     actual reviewer response time from the share time forward.
   - If not found: note the gap factually as "gap between PR open and first
     review" without characterizing it as a reviewer response time issue.

If the ticket was re-opened after being marked Done, call this out explicitly: "Ticket was marked Done prematurely and reopened."

### Step 5 — Analyze review comments

Read every review comment on every PR. Classify each comment into one of:

| Category                | Description                                                                      |
| ----------------------- | -------------------------------------------------------------------------------- |
| **Late requirement**    | A functional behavior that should have been in the ticket's acceptance criteria  |
| **Codebase convention** | A pattern or helper that exists in the codebase and was unknown to the developer |
| **Style / naming**      | A preference about naming, structure, or readability                             |
| **Bug found**           | A correctness defect caught in review                                            |
| **Out of scope**        | Something deferred to a follow-up ticket                                         |

Quote the actual comment text (truncated to ~100 words if long). Note the commenter's name and PR number.

**Codebase convention vs. tribal knowledge**: If a convention is documented in CLAUDE.md, a README, or a linked style guide, note that. If it exists only as an example in the codebase and was never written down, flag it as **undocumented convention** — these are candidates for documentation.

### Step 6 — Write the per-ticket report

Determine the report's subdirectory from the month the ticket moved to `Done` (format: `YYYY-MM`). Write the report to `<OUTPUT_DIR>/<YYYY-MM>/<TICKET-ID>.md`. Create the subdirectory if it does not exist.

**Tone**: Address the reader as the person who wrote the ticket. Use "you" and "your." Write as a thoughtful peer, not an auditor. The goal is "here's what would have made this easier" — not "here's what went wrong."

Use this structure:

```markdown
# <TICKET-ID>: <Title>

**Requested by**: <reporter display name>
**Description editors**: <comma-separated list of display names who changed the description field after creation, from changelog/history — omit this line if no edits>
**Data confidence**: Full | Partial | <TRACKER_LABEL>-only
**PRs found**: N (via native tracker link | GitHub search)
**PR traceability**: Linked proactively ✓ | Found only via text search ✗

## Timeline

| Metric              | Value    |
| ------------------- | -------- |
| Implementation time | X days   |
| Total elapsed       | X days   |
| Review rounds       | N        |
| Premature Done?     | Yes / No |

[If premature Done: call out explicitly.]

[If 3+ day review gaps: note each one with dates, without speculating on cause.]

## What emerged during review

### Requirements discovered late

[One paragraph or bullet list per requirement. Quote the comment that surfaced it.
Explain why it matters — what would have gone wrong without that comment.]

### Codebase conventions you weren't pointed to

[List conventions surfaced in review. For each: what it is, where to find it,
and whether it is documented anywhere. Flag undocumented conventions.]

### Style and naming feedback

[Brief list. These are usually low-stakes but worth noting for patterns.]

### Bugs caught in review

[If any. Be factual, not judgmental.]

## How the implementation diverged from the ticket

[Table or bullet list: what the ticket said vs. what shipped. Keep it factual.]

## If you were starting over

This section is written as if the ticket were being reopened today and you
were handing it to yourself from before you started.

[Rewrite the ticket using the project's bug template structure as a model.
If no feature template exists, use the section order: Background, Data model
notes (if relevant), Behavior specification, Acceptance criteria, Code
conventions to follow.]

When writing the rewritten ticket:

- Use plain, direct English. Avoid passive voice.
- Spell out abbreviations on first use.
- Prefer bullet points over prose for acceptance criteria.
- Each acceptance criterion should be independently testable.
- Do not assume the reader knows the codebase conventions — point to them explicitly.
```

### Step 7 — Return results to parent

Return a structured summary to the parent agent containing:

- Ticket ID
- Data confidence level
- PR traceability (linked / text-search only / none)
- Count of late requirements found
- Count of undocumented conventions found
- Implementation time (days)
- Total elapsed time (days)
- Whether the ticket was prematurely closed
- Whether a feature template exists in the tracker

---

## Step 8 — Write aggregate summary

After all subagents complete, write `<OUTPUT_DIR>/summary.md`.

```markdown
# Story Retro Summary

**Run date**: <today>
**Scope**: <the native query or ticket list used>
**Tickets analyzed**: N

## PR Traceability

- N of M tickets had PRs discoverable via the tracker's native link
- N of M tickets required text search to find PRs
- N of M tickets had no discoverable PRs

_Recommendation if < 80% linked via the native tracker link_: Ask the team to link PRs to
tickets when opening them. This takes 10 seconds and dramatically improves traceability.

## Ticket Template

- Feature ticket template: exists | **does not exist**
- Bug ticket template: exists | does not exist

_If no feature template_: The rewritten tickets in this report collectively
illustrate what a feature template could look like. Consider proposing one
using those as examples.

## Recurring Patterns Across Tickets

List themes that appeared in 2+ tickets. Group by category:

### Late requirements (appeared in N tickets)

[Describe the pattern — e.g., "Data model structure was described in
terms of desired outcome but not table shape or row counts."]

### Undocumented conventions (appeared in N tickets)

[Name each convention and how many tickets it appeared in. These are
candidates for adding to CLAUDE.md or a developer onboarding doc.]

### Premature Done

[N tickets were marked Done and reopened. List them.]

## Per-Ticket Summary Table

| Ticket   | Confidence | PRs | Impl. days | Total days | Late reqs | Undoc. conventions |
| -------- | ---------- | --- | ---------- | ---------- | --------- | ------------------ |
| XYZ-XXXX | Full       | 3   | 4          | 12         | 2         | 1                  |
```

## Notes on scope

- **Pairing**: When a ticket has PRs from multiple authors, analyze all PRs. The ticket is the unit of analysis, not the developer.
- **External code owners**: Note in the per-ticket timeline when a review came from outside the immediate team. Do not editorialize about the delay — just note it factually.
- **`<TRACKER_LABEL>`-only tickets**: Still produce a report. Analyze ticket quality (clarity of AC, presence of data model notes, etc.) and write a rewritten ticket based on what can be inferred from the ticket's own discussion alone.
