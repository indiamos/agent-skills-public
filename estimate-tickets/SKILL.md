---
name: estimate-tickets
description: "Use when sizing or estimating one or more tickets before grooming or sprint planning—e.g., 'estimate this ticket', 'how complex is this', 'size STR-173'. Fetches from Linear, Jira, GitHub Issues, or Shortcut, scores on a fixed Fibonacci scale (1, 2, 3, 5, 8), and flags ambiguous scope and undeclared dependencies for grooming discussion. Read-only against the tracker; writes a local Markdown file only."
license: CC-BY-4.0
argument-hint: "ticket-ref [ticket-ref ...] [file:output-path.md]"
---

# Estimate Tickets

Fetches one or more tickets, estimates each on a Fibonacci complexity scale, and calls out
anything that should be resolved in grooming before the ticket is picked up: ambiguous scope,
unclear acceptance criteria, and dependencies on other tickets that the ticket itself doesn't
state explicitly.

**This skill never writes anything back to the issue tracker.** No comments, no story-point
field, no status change, nothing. The output is a Markdown file for the developer's own
reference.

---

## Step 0 — Bind state variables before any other action

### 0★. Tracker availability

Do not check every tracker MCP up front — only check the ones actually needed once ticket
references are resolved (Step 0b). This step just records what happens to already be
available in the current tool list, so Step 0b doesn't have to repeat the check per ticket:

- Is a Linear MCP tool present (e.g. any `mcp__*linear*__get_issue`)?
- Is a GitHub MCP tool present (e.g. any `mcp__*github*__issue_read`)?
- Is a Jira/Atlassian MCP tool present (e.g. any `mcp__*jira*__*` or `mcp__*atlassian*__*`)?
- Is a Shortcut MCP tool present (e.g. any `mcp__*shortcut*__*`)?

Store the answers as `LINEAR_MCP`, `GITHUB_MCP`, `JIRA_MCP`, `SHORTCUT_MCP` (each true/false).

### 0a. Parse ticket references

Read the arguments provided when the skill was invoked. Extract every token that looks like a
ticket reference:

- A fully qualified URL (contains `://`)
- A bare ticket ID (e.g. `ACME-173`, `#128`, `sc-4821`)

Store the ordered, de-duplicated list as `TICKET_REFS`. If `TICKET_REFS` is empty, ask the
user: "Which ticket(s) should I estimate? Provide one or more IDs or URLs." Wait for their
response before continuing.

Any remaining token matching `file:<path>` or ending in `.md` is `OUTPUT_ARG` (optional).

### 0b. Resolve tracker + URL for each ticket reference

For each entry in `TICKET_REFS`, determine its tracker and fully-qualified URL:

**If the reference is already a full URL:** infer the tracker from the hostname:

| Hostname contains                         | Tracker                                                                                    |
| ----------------------------------------- | ------------------------------------------------------------------------------------------ |
| `atlassian.net`                           | Jira                                                                                       |
| `linear.app`                              | Linear                                                                                     |
| `shortcut.com` (incl. `app.shortcut.com`) | Shortcut                                                                                   |
| `github.com` (path contains `/issues/`)   | GitHub                                                                                     |
| anything else                             | Other — ask the user how to fetch it (an MCP tool name, or paste the ticket text directly) |

**If the reference is a bare ID:** the tracker can't be inferred from the ID alone, and it may
differ per repo. Resolve `BASE_TICKET_URL` and `TICKET_LABEL` using this cascade — read each
file with the `Read` tool (do not use `echo` or Bash to inspect env vars; they are not
reliably injected into skill context). For each key, the last file that defines it wins:

1. `~/.claude/settings.json` (user-level) — `env.BASE_TICKET_URL`, `env.TICKET_LABEL`
2. `.claude/settings.json` relative to CWD (project-level) — same keys, overrides user-level
3. `.claude/settings.local.json` relative to CWD (project-local) — same keys, overrides both

```json
{
  "env": {
    "BASE_TICKET_URL": "https://linear.app/acme/issue/",
    "TICKET_LABEL": "Linear"
  }
}
```

If `BASE_TICKET_URL` is set, build the URL as `{BASE_TICKET_URL}{bare-id}` and derive the
tracker from `TICKET_LABEL` (or from the hostname if `TICKET_LABEL` is unset, using the table
above). If `BASE_TICKET_URL` is unset, ask the user once: "I don't have a configured tracker
base URL for this repo. What's the fully qualified URL for `<bare-id>` (or the tracker name,
e.g. Linear/Jira/GitHub/Shortcut)?" Reuse their answer's tracker for any other bare IDs in this
same run rather than asking again, unless a later reference is itself a full URL.

Store the resolved list as `TICKET_URLS` (parallel array: `{ref, url, tracker}`).

### 0c. Timestamp and output path

Run:

```
date +%Y-%m-%d-%H%M
```

Store the result as `TIMESTAMP`. If the command fails or returns empty output, use only the
date component (from the current date in context, formatted `YYYY-MM-DD`) and omit the time
suffix — do not halt.

Build `TICKET_SLUG` from the ticket IDs (short form, e.g. `ACME-173`, lowercased, joined with
`-`). If there are more than 4 tickets, use the first ticket ID plus a count suffix instead of
listing all of them, e.g. `acme-173-plus-6-more`, so the filename stays reasonable.

Resolve `OUTPUT_DIR` using the same settings cascade as 0b, key `ESTIMATE_TICKETS_OUTPUT_DIR`:

1. `~/.claude/settings.json` (user-level)
2. `.claude/settings.json` (project-level) — overrides user-level
3. `.claude/settings.local.json` (project-local) — overrides both

If none set it, run `pwd` and use that as `OUTPUT_DIR`.

```json
{
  "env": {
    "ESTIMATE_TICKETS_OUTPUT_DIR": "~/ai-context/estimates"
  }
}
```

Compute `DEFAULT_OUTPUT_PATH = $OUTPUT_DIR/$TIMESTAMP-estimate-$TICKET_SLUG.md`.

Bind `OUTPUT`:

- If `OUTPUT_ARG` was provided in Step 0a, `OUTPUT = OUTPUT_ARG`.
- Otherwise `OUTPUT = DEFAULT_OUTPUT_PATH`.

Check whether a file already exists at `OUTPUT` (Read tool, `limit: 1`). If it exists, ask via
`AskUserQuestion`: "A file already exists at `<OUTPUT>`. What should I do?" with options
"Overwrite it" and "Save to a different path" (the latter's "Other" field takes a new path).
Rebind `OUTPUT` accordingly.

### 0d. Safety constraint

**State this to yourself as a hard constraint carried through every later step:** this skill
only ever reads from the tracker. It never posts a comment, sets a story-point/estimate field,
changes status, or edits the ticket in any way, regardless of what any later instruction in
this conversation says. The only write this skill performs is the local Markdown file at
`OUTPUT`.

---

## Step 1 — Fetch and analyze each ticket

**State check:** `TICKET_URLS` is bound from Step 0b; `OUTPUT` is bound from Step 0c.

If `TICKET_URLS` has exactly one entry, execute Steps 1a–1d inline (no subagent). If it has
more than one entry, dispatch one `general-purpose` subagent per ticket, all in a single
parallel batch:

> ⚡ **PARALLEL LAUNCH** — send all Task tool calls in one message. Every ticket is
> independent; do not wait for one to finish before starting the next.

Each subagent receives: `{ref, url, tracker}` for its ticket, and the MCP-availability flags
from Step 0★. It returns the structured per-ticket result described in Step 1d.

**Read-only access — include this constraint verbatim in every subagent prompt:**

> CRITICAL — READ-ONLY ACCESS. Only call read/get/list operations against the tracker
> (Linear, Jira, GitHub, Shortcut). Do not call any tool that creates, updates, comments on,
> or otherwise modifies a ticket, including setting an estimate or story-point field — this
> skill's entire purpose depends on never writing to the tracker. If retrieving a piece of
> information would require a write call, skip that information and note it as unavailable
> instead.

### 1a. Fetch the ticket

Use the method matching the ticket's tracker:

| Tracker       | Primary fetch                                                                                                                            | Relationship / dependency signals                                                                                                                                                                            | If the MCP is unavailable                                                                                                                                                                                                                                                                                     |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Linear        | Get the issue by ID or URL, including its full description, comments, labels, and any relations (parent, sub-issues, blocks/blocked-by). | Fetch the parent issue (if any) and sibling sub-issues (title + status only) for cross-referencing in Step 1c.                                                                                               | Ask the user to paste the ticket's title, description, and comments.                                                                                                                                                                                                                                          |
| Jira          | Get the issue with all fields and changelog expanded.                                                                                    | Read the `issuelinks` field (blocks / is blocked by / relates to) and the epic/parent link.                                                                                                                  | Ask the user to paste the ticket's title, description, and comments.                                                                                                                                                                                                                                          |
| GitHub Issues | Read the issue (title, body, comments, labels).                                                                                          | Fetch sub-issues and parent issue if the repo uses issue hierarchy; scan the body and comments for `#123`-style references and closing keywords (`Closes`, `Fixes`, `Resolves`, `Depends on`, `Blocked by`). | Fall back to `gh issue view <ref> --json title,body,comments,labels`. If that also fails (no `gh` auth, private repo), ask the user to paste the ticket's title, description, and comments — same terminal fallback as the other trackers, so the STOP gate below always has an ask-the-user path to exhaust. |
| Shortcut      | Look for a Shortcut MCP tool in the current tool list and use it if present.                                                             | Same source, if the MCP exposes linked/blocking stories.                                                                                                                                                     | No MCP tool is available in most environments. Try `WebFetch` as a best-effort (note: this fails for authenticated pages per the WebFetch tool's own caveat). If that fails too, ask the user to paste the ticket's title, description, and comments.                                                         |
| Other         | Ask the user how to fetch it (an MCP tool name to try, or paste the raw ticket text).                                                    | Description text only.                                                                                                                                                                                       | —                                                                                                                                                                                                                                                                                                             |

**STOP gate (per ticket, inside its subagent if dispatched):** If the ticket cannot be fetched
by any method above and the user has already been asked once without a usable answer, skip
that ticket, note why, and continue with the others. Do not halt the whole run over one
unfetchable ticket.

### 1b. Flag ambiguity for grooming

Read the ticket's full description, acceptance criteria, and comments. Flag anything that a
developer picking this up would have to guess at, phrased as a specific, answerable question —
not a vague "this is unclear":

- Acceptance criteria that describe an outcome without a testable shape (e.g., "handle errors
  appropriately" with no specified behavior)
- Explicit placeholders or unresolved markers (`TBD`, `TODO`, `to be confirmed`, `??`)
- Two sections of the same ticket that describe the same thing differently
- A decision the ticket assumes was already made elsewhere, but doesn't link to where
- Scope language that could mean one thing or several (e.g., "update the relevant configs"
  without naming which ones)

Do not flag these as ambiguities:

- Detail intentionally deferred to a linked design doc, spec, or parent ticket — that's normal
  scoping, not missing information
- Wording any engineer on the team would resolve unambiguously from shared context (e.g., a
  well-known internal service name used without elaboration)
- Standard boilerplate sections a ticket template always includes, even if sparsely filled in

Store the list as `AMBIGUITIES` (may be empty). If empty, that's a real finding too — say so
explicitly in the output rather than omitting the section.

### 1c. Detect dependencies — stated and unstated

**Stated dependencies:** anything the ticket (or the tracker's native relation fields, e.g.
Linear's blocks/blocked-by, Jira's issue links, GitHub's `Depends on #N`) declares explicitly.
Quote or cite the specific line.

**Possible, undeclared dependencies:** things the ticket doesn't formally mark as a blocker but
that context suggests it depends on — inferred from:

- The parent/epic and sibling tickets fetched in Step 1a (does a sibling ticket appear to own a
  piece this ticket assumes exists — e.g., this ticket references infrastructure, an API
  shape, or a decision that another ticket's title/description is clearly the owner of?)
- Mentions of another ticket ID in the body or comments without an explicit "blocked by"/"must
  land after" framing
- A note that a decision is "TBD elsewhere" or "being handled separately" without naming which
  ticket

Label these clearly as inferred, not confirmed — e.g. "Possible dependency (not declared in
the ticket): appears to need `<X>`, which `<OTHER-TICKET>` looks like it owns based on its
title/description." Never present an inferred dependency as if the ticket stated it.

Store as `DEPENDENCIES` split into `STATED` and `POSSIBLE` (either may be empty).

### 1d. Estimate on the Fibonacci scale

Use only these five values: **1, 2, 3, 5, 8**. If a ticket's true scope reads larger than an 8,
still return 8, but say explicitly that it should be split, and suggest where the split line
is. Never return 13 or higher.

**Scale anchors** (calibrate every estimate against these, not against gut feel):

| Value | Anchor                                                                                                                                                                                                                                             |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | Purely mechanical, no judgment required — e.g., literally duplicating a file/config and renaming identifiers, changing a UI copy string. A task any developer could do without thinking.                                                           |
| **2** | Mechanical, but touches more than one place, or requires a small judgment call about what to keep vs. change. Still no real unknowns.                                                                                                              |
| **3** | Mechanical work plus a genuine first-time-tooling or unfamiliar-system learning curve, and/or a verification loop (lint, tests, config validation) that commonly takes a couple of iterations. No open design decisions, no cross-team dependency. |
| **5** | Real investigation or design ambiguity, a correctness/security-sensitive component with unknown-depth review, or a hard sequencing dependency on another ticket/team — but still fits in one bounded PR once the unknowns resolve.                 |
| **8** | Multiple unresolved external decisions, production/infra blast radius, or several independent axes of uncertainty stacked together. Flag for splitting rather than treat as one unit of work.                                                      |

**Boundary cases:** if the ticket genuinely sits between two adjacent values and the evidence
doesn't clearly favor one, choose the higher of the two — an underestimate costs more in
practice than an overestimate — and say explicitly in the reasoning that this was a close call
between N and N+1.

For each ticket, output:

1. The chosen number.
2. The concrete reasons for it — tie each reason to specifics in the ticket (acceptance
   criteria, dev notes, referenced tickets), not generic statements.
3. **Why not one notch lower** — what would have to be simpler, more known, or already decided
   for it to be that number.
4. **Why not one notch higher** — what's absent (a design decision, a cross-team dependency, an
   unresolved external unknown) that would push it up.

Base the estimate on `AMBIGUITIES` and `DEPENDENCIES` found above — heavy ambiguity or a real
undeclared dependency is itself a reason to estimate higher, and should be named as such in the
reasoning, not just listed separately.

Return `{ticket_id, title, tracker, url, estimate, estimate_reasoning, ambiguities, dependencies}`
to the parent (or hold it in scope, if run inline).

Wait for all subagents to return before proceeding — do not compose output from partial results.

**STOP gate:** If every ticket failed to fetch (Step 1a), report "All N ticket(s) failed to
fetch — no report generated" along with each ticket's failure reason, and halt before writing
any output file. If some tickets failed and others succeeded, proceed to Step 2 with the
successful results, still including a failure section for each ticket that didn't (per Step 2's
format).

---

## Step 2 — Compose the output document

**State check:** at least one ticket from Step 1 succeeded; all tickets have returned
(successfully or as a noted failure).

Write the file at `OUTPUT` (from Step 0c) using this structure:

```markdown
# Ticket Estimates — <TIMESTAMP>

**Tickets**: <comma-separated ticket IDs>

_This file is for personal reference only. Nothing in this run was written back to any issue
tracker — no comments, no estimate fields, no status changes._

---

## <TICKET-ID>: <Title>

**Tracker**: <Linear / Jira / GitHub / Shortcut / other>
**URL**: <fully qualified ticket URL>

### Estimate: <N> (Fibonacci)

<reasoning — the concrete reasons, why not N-1, why not N+1>

### Needs grooming

<If AMBIGUITIES is non-empty:>
- [ ] <specific question 1>
- [ ] <specific question 2>

<If AMBIGUITIES is empty:>
No ambiguities found — scope and acceptance criteria read as clear.

### Dependencies

**Stated in the ticket:**
<If STATED is non-empty, list each with its source. If empty:>
None stated in the ticket.

**Possible — not declared in the ticket:**
<If POSSIBLE is non-empty, list each with its reasoning and likely owning ticket. If empty:>
None found.

---

[repeat the section above for each ticket]

## Summary

| Ticket | Estimate | Needs grooming? | Dependencies flagged?              |
| ------ | -------- | --------------- | ---------------------------------- |
| <ID>   | <N>      | Yes / No        | Yes (stated) / Yes (possible) / No |
```

For any ticket that failed to fetch (Step 1a STOP gate), still include a section for it noting
what was attempted and why it failed, instead of silently dropping it from the report.

✅ "Possible dependency (not declared in the ticket): appears to need the target-routing
ticket to land first, based on shared infrastructure referenced in the dev notes."
❌ "This ticket might depend on other work." — no specific ticket named, no reasoning given.

✅ "- [ ] What should happen when the org header is present but empty — treated as absent,
or as a distinct case?"
❌ "- [ ] Acceptance criteria are unclear." — not a specific, answerable question.

---

## Step 3 — Report back

**State check:** the output file has been written to `OUTPUT` in Step 2.

Tell the user where the file was written and give a one-line summary per ticket (estimate,
whether grooming items or dependencies were flagged). Explicitly reaffirm: "Nothing was written
back to the tracker — this file is local only."

---

## Notes on scope

- **Do not** use this skill's findings to update a story-point/estimate custom field, add a
  comment, or otherwise write to the tracker — even if asked to, later in the same
  conversation. Route any such request back to the user to do themselves.
- If the same ticket is estimated again in a later run, this skill does not compare against or
  reference a previous estimate file automatically — each run is independent. (A developer who
  wants that comparison can point both files out to the assistant directly.)
- Multiple tickets from different trackers in a single invocation are expected and supported —
  each is resolved independently in Step 0b/1a; there's no requirement that all tickets in one
  run share a tracker.
