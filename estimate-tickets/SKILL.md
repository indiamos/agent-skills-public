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

Do not check every tracker MCP up front — check only the ones actually needed once ticket
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

## Step 1 — Fetch and flag each ticket

**State check:** `TICKET_URLS` is bound from Step 0b; `OUTPUT` is bound from Step 0c.

If `TICKET_URLS` has exactly one entry, execute Steps 1a–1c inline (no subagent). If it has
more than one entry, dispatch one `general-purpose` subagent per ticket, all in a single
parallel batch:

> ⚡ **PARALLEL LAUNCH** — send all Task tool calls in one message. Every ticket is
> independent; do not wait for one to finish before starting the next.

Each subagent receives: `{ref, url, tracker}` for its ticket, and the MCP-availability flags
from Step 0★. It returns the structured per-ticket result described at the end of Step 1c.
Scoring happens later, in Step 3, after Step 2 gives the requester a chance to resolve the
ambiguities this step flags — a subagent here only fetches and flags, it doesn't estimate.

**Read-only access — include this constraint verbatim in every subagent prompt:**

> CRITICAL — READ-ONLY ACCESS. Call only read/get/list operations against the tracker
> (Linear, Jira, GitHub, Shortcut). Do not call any tool that creates, updates, comments on,
> or otherwise modifies a ticket, including setting an estimate or story-point field — this
> skill's entire purpose depends on never writing to the tracker. If retrieving a piece of
> information would require a write call, skip that information and note it as unavailable
> instead.

### 1a. Fetch the ticket

Use the method matching the ticket's tracker:

| Tracker       | Primary fetch                                                                                                                            | Relationship / hierarchy fetch (used in both 1b and 1c)                                                                                                                                                       | If the MCP is unavailable                                                                                                                                                                                                                                                                                     |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Linear        | Get the issue by ID or URL, including its full description, comments, labels, and any relations (parent, sub-issues, blocks/blocked-by). | Fetch the parent issue's full description and comments (if any), and sibling sub-issues (title + status only).                                                                                              | Ask the user to paste the ticket's title, description, and comments.                                                                                                                                                                                                                                          |
| Jira          | Get the issue with all fields and changelog expanded.                                                                                    | Fetch the epic/parent issue's full description and comments via the epic/parent link, and read the `issuelinks` field (blocks / is blocked by / relates to).                                                | Ask the user to paste the ticket's title, description, and comments.                                                                                                                                                                                                                                          |
| GitHub Issues | Read the issue (title, body, comments, labels).                                                                                          | Fetch the parent issue's full body and comments if the repo uses issue hierarchy, plus sub-issue titles; scan the body and comments for `#123`-style references and closing keywords (`Closes`, `Fixes`, `Resolves`, `Depends on`, `Blocked by`). | Fall back to `gh issue view <ref> --json title,body,comments,labels`. If that also fails (no `gh` auth, private repo), ask the user to paste the ticket's title, description, and comments — same terminal fallback as the other trackers, so the STOP gate below always has an ask-the-user path to exhaust. |
| Shortcut      | Look for a Shortcut MCP tool in the current tool list and use it if present.                                                             | Same source, if the MCP exposes a parent story's full content and linked/blocking stories.                                                                                                                  | No MCP tool is available in most environments. Try `WebFetch` as a best-effort (note: this fails for authenticated pages per the WebFetch tool's own caveat). If that fails too, ask the user to paste the ticket's title, description, and comments.                                                         |
| Other         | Ask the user how to fetch it (an MCP tool name to try, or paste the raw ticket text).                                                    | Description text only.                                                                                                                                                                                       | —                                                                                                                                                                                                                                                                                                             |

This parent/epic fetch is a full read, not a title-only skim — it's the same depth as the
ticket's own description, because Step 1b depends on actually being able to answer questions
from it, not just detect its existence.

**Unfetchable ticket (per ticket, inside its subagent if dispatched):** If the ticket cannot be
fetched by any method above and the user has already been asked once without a usable answer,
skip that ticket and note why in its result — this is a per-ticket skip, not a halt, so the
other tickets in this run continue normally.

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

**Before adding anything to `AMBIGUITIES`, check whether the parent/epic ticket fetched above
already answers it.** This is a forced check, not a judgment call to skip because the answer
feels like it's probably deferred upward — actually read the parent's description and comments
for the specific point in question, and check sibling sub-issue titles/status for a ticket that
clearly owns it. If the parent (or a sibling) answers it, do not add it to `AMBIGUITIES` —
instead record it in `PARENT_RESOLVED` as `{question, answer, source}`, where `source` is the
parent/sibling ticket ID and the relevant section. Label it as resolved by ticket hierarchy, not
assumed — e.g. "Answered by parent ACME-100: acceptance criteria there specify org-header-absent
handling for the whole epic." Only what the parent doesn't cover falls through to the checks
below.

Do not flag these as ambiguities:

- Detail intentionally deferred to a linked design doc or spec (not the parent ticket — that
  gets the forced check above, not a pass) — that's normal scoping, not missing information
- A term or name used without definition that already appears, defined or used consistently,
  elsewhere in this same ticket, its parent, or a linked doc — e.g., a service name the parent
  ticket already names, or an abbreviation the ticket itself expands on first use
- Standard boilerplate sections a ticket template always includes, even if sparsely filled in

Store the list as `AMBIGUITIES` (may be empty) and `PARENT_RESOLVED` (may be empty). If
`AMBIGUITIES` is empty, that's a real finding too — say so explicitly in the output rather than
omitting the section.

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

**Classify every dependency found — stated or possible — as `sequencing` or `risk`:**

- **Sequencing:** the dependency's shape is already fully defined and stable; the only thing
  outstanding is that it hasn't merged, deployed, or been picked up yet. You're waiting, not
  exposed to rework.
- **Risk:** the dependency's shape could still change before this ticket can be built against
  it — a contract still under review, a spec not finalized, a decision the owning team hasn't
  made yet.

Apply this test: if the estimate would drop the moment the dependency merges, with no
other change, it's sequencing, not risk — a ready-state fact, not a complexity fact. Only risk
carries weight in Step 4's estimate.

For each dependency, store `{description, source, kind: sequencing|risk, reason}`, where
`reason` is a one-line justification for the classification — e.g. "sequencing only — shape
already fully defined in ACME-200" or "risk — PR is still under review, contract could shift."

Store as `DEPENDENCIES` split into `STATED` and `POSSIBLE` (either may be empty), each entry
carrying its `kind` and `reason`.

Return `{ticket_id, title, tracker, url, ticket_context, ambiguities, parent_resolved,
dependencies}` to the parent (or hold it in scope, if run inline). `ticket_context` is a compact
digest — title, the acceptance-criteria points that bear on complexity, and any comment content
relevant to scope — enough for Step 4 to estimate and Step 5 to recommend ticket edits without
re-fetching the ticket. Keep every acceptance-criteria bullet, dev-note bullet, and context
sentence that bears on complexity **verbatim, not paraphrased** — Step 5 needs to quote them
exactly when proposing a reworded version.

Wait for all subagents to return before proceeding to Step 2 — do not act on partial results.

**STOP gate:** If every ticket failed to fetch (Step 1a), report "All N ticket(s) failed to
fetch — no report generated" along with each ticket's failure reason, and halt before writing
any output file. If some tickets failed and others succeeded, proceed to Step 2 with the
successful results, still including a failure section for each ticket that didn't (per Step 6's
format).

---

## Step 2 — Check the codebase before asking the requester

**State check:** `AMBIGUITIES` is bound per ticket from Step 1.

Skip this step if every ticket's `AMBIGUITIES` is empty — go straight to Step 3. Many grooming
questions are actually answerable from the repo(s) the requester is already sitting in — an
existing pattern, a config value, a sibling endpoint's behavior, or the repo layout itself. Check
those before bothering the requester with something the code already settles.

### 2a. Resolve search scope (once — not per ticket)

Run `pwd` to get `LAUNCH_DIR`. Then run `git -C "$LAUNCH_DIR" rev-parse --show-toplevel`:

- **If it succeeds:** the requester launched from inside a single repo. `REPO_ROOTS = [<that
  toplevel path>]`, `REPO_SCOPE = single-repo`.
- **If it fails:** `LAUNCH_DIR` isn't itself a repo — it may be a folder of related repos (the
  requester's other common pattern). List `LAUNCH_DIR`'s immediate subdirectories (one level
  deep only, don't recurse further) and keep the ones containing a `.git` entry. If that list is
  non-empty, `REPO_ROOTS = <that list>`, `REPO_SCOPE = multi-repo`.
- **If neither applies:** `REPO_ROOTS = []`, `REPO_SCOPE = none`. Skip the rest of this step for
  every ticket — there's nothing to search — and proceed to Step 3 with `AMBIGUITIES` unchanged.

If `REPO_SCOPE = multi-repo` and there are more than ~20 sibling repos, don't blindly search all
of them — narrow to the ones whose directory name plausibly matches a service/product-area term
from the ticket titles or descriptions, and note in the output (Step 6) which repos were
actually searched.

### 2b. Search for answers, per ticket

For each ticket with a non-empty `AMBIGUITIES`, and for each entry in it, judge whether the
question has a code angle at all — "what does X currently do," "does Y already exist," "which
service owns Z," "is there already a pattern for W," and even scope-boundary questions like
"should this be split along service lines" (the repo's actual package/service boundaries are
themselves evidence). Skip questions that are pure product or prioritization calls with no
possible code answer (e.g., "should we do this before or after the other initiative").

Search `REPO_ROOTS` with `Grep`/`Glob`/`Read` for: existing implementations, config values, or
flags the question is asking about; comments (`TODO`, `FIXME`) or code referencing this ticket's
ID; the repo/package boundaries relevant to a scope-splitting question; prior art from a similar
feature that already settled the same "how should this behave" question. If there's more than
one ticket, this can run as one `general-purpose` subagent per ticket, dispatched in parallel
(same pattern as Step 1):

> ⚡ **PARALLEL LAUNCH** — send all Task tool calls in one message if dispatching subagents here.

Each dispatched subagent must return `{ticket_id, code_resolved, ambiguities}` to the parent —
`code_resolved` is its ticket's `CODE_RESOLVED` list, `ambiguities` is what's left of that
ticket's `AMBIGUITIES` after the search — so the parent can merge results without re-deriving
which questions were answered.

**Cap the effort at 3 targeted searches per question — this is a quick check, not an
investigation.** If a question isn't answered within those 3 (e.g., 3 `Grep`/`Glob` calls
covering different terms), mark it unresolved and move on — an unbounded search here is exactly
the investigation Step 2 is meant to avoid.

For any question the code answers with reasonable confidence, move it out of that ticket's
`AMBIGUITIES` and into `CODE_RESOLVED` as `{question, answer, source}`, where `source` is the
file path (and line number, where practical) backing the answer. Label these as inferred from
the repo, not confirmed by the ticket or the requester — e.g. "Answered from code
(`services/api/router.go:42`): the org header is already treated as absent when empty for the
sibling `/v2/session` endpoint." Never present a code-derived answer as if the ticket or
requester stated it. Anything the search can't resolve, or that has no code angle, stays in
`AMBIGUITIES` unchanged.

Store `CODE_RESOLVED` per ticket (may be empty).

---

## Step 3 — Check in on grooming questions before estimating

**State check:** every ticket from Step 1 has returned, with `AMBIGUITIES` (possibly empty) and
`DEPENDENCIES` bound per ticket; Step 2 has run (or been skipped), leaving `AMBIGUITIES` reduced
by anything moved into `CODE_RESOLVED`.

If every ticket's `AMBIGUITIES` list is empty, skip this step and go straight to Step 4 — there's
nothing left to check in on.

Otherwise, ask the requester about the outstanding questions before scoring anything, since
they can often answer at least some of them on the spot — that's real signal, and asking first
means the estimate doesn't have to be redone once grooming happens anyway. Present the
questions grouped by ticket in one message, phrased as an invitation to answer what they
already know rather than a blocker:

```
Before I estimate these, a few things came up that grooming would normally catch. Answer
whatever you already know — anything left goes into the doc as a grooming item:

ACME-173
- What should happen when the org header is present but empty?

ACME-175
- Does "update the relevant configs" include the staging config, or prod only?
```

Skip re-asking about anything the requester already addressed earlier in this conversation
(e.g., in their original request) — check before asking, don't make them repeat themselves.

Wait for the requester's response before continuing. For each answer that resolves a listed
question, move it out of that ticket's `AMBIGUITIES` and into `RESOLVED` as `{question,
answer}`. Anything left unaddressed stays in `AMBIGUITIES` unchanged — a partial or absent
response is a valid outcome, not a reason to re-ask.

**A reply is not, by itself, permission to move to Step 4.** Answering some or even all of the
questions is not the same as being done — the requester may still be mid-thought, may want to
add more context, or may have follow-up questions of their own about what you found. Don't
treat a substantive-looking reply as an implicit go-ahead. After incorporating whatever they
said, check in explicitly: "Anything else on these, or should I go ahead and estimate?" and wait
for a real answer. Proceed to Step 4 only once the requester gives an explicit go-ahead ("that's
all," "go ahead," "proceed," etc.) — not merely because they replied. If they give more
clarification instead, incorporate it the same way (updating `RESOLVED`/`AMBIGUITIES`, and
re-running Step 2's codebase check on anything new worth checking) and ask again. This can
repeat as many times as the requester needs; there's no cap on rounds, only on letting silence
or a partial answer stand in for confirmation.

Store `RESOLVED` per ticket (may be empty).

---

## Step 4 — Estimate each ticket

**State check:** `ticket_context`, `AMBIGUITIES`, `PARENT_RESOLVED`, and `DEPENDENCIES` are
bound per ticket from Step 1; `CODE_RESOLVED` is bound per ticket from Step 2 (empty if
skipped); `RESOLVED` is bound per ticket from Step 3 (empty if skipped).

Use only these five values: **1, 2, 3, 5, 8**. If a ticket's true scope reads larger than an 8,
still return 8, but say explicitly that it should be split — subject to the tests below — and
suggest where the split line is. Never return 13 or higher.

If a sibling file named `SKILL.<company>.md` exists in this skill's directory, check it now: a
company rider may define a different client-facing point scale. When one does, keep reasoning
against the canonical five tiers below exactly as written — the anchors, the split tests, and
every "why not one notch lower/higher" judgment are about tier position, not about the numbers
1/2/3/5/8 themselves. Only translate the final chosen tier to the rider's scale, using its
mapping table, when storing `ESTIMATE` and when composing Step 6's output. Everywhere else in
this skill — including this step's own prose — "8" means "the top tier, flag for split" and
should be read as the rider's top value where one applies.

**Deciding whether to recommend a split — three separate tests, not one.** First identify *why*
the ticket reads as an 8, using the `risk`-classified dependencies from Step 1c and the
ticket's own scope signals (files/services touched, infra blast radius it names):

- **Risk-stacked** — the 8 comes from stacked `risk` dependencies. Apply the **actionability
  test** below.
- **Breadth-driven** — the 8 comes from mechanical scope (many files/services, infra blast
  radius) with no `risk` dependency behind it. Apply the **value-boundary test** below.
- **Mixed** — both are present. Run the actionability test against the risk portion first; only
  if it finds no valid split, separately run the value-boundary test against the breadth
  portion.

*Actionability test (risk-stacked 8s).* A split pays for itself only if some resulting piece
clears both gates below — not just a piece with fewer risks by count:

1. **Durability gate** — classify the piece by how much of it would survive the dependency
   resolving, using these tiers instead of a gut call about what's "likely":
   - *Tier 0 — untouched.* The piece's logic never touches the unresolved surface at all.
   - *Tier 1 — call-site only.* Built against the dependency's current draft; if the draft
     shifts, only the call site/adapter needs rework, not the piece's internal design.
   - *Tier 2 — not durable.* The piece's core design, data model, or control flow depends on
     how the unresolved thing resolves.
   Only Tier 0 or Tier 1 clears this gate. A piece stuck at Tier 2 never clears it, however few
   risks it carries relative to the whole ticket.
2. **Materiality gate** — estimated on its own, would that Tier 0/1 piece be at least a 2
   (touches more than one place, or needs a small judgment call), not a 1-point stub?

- Some piece clears both gates → recommend the split; name the piece and its tier.
- Every piece is stuck at Tier 2 → don't split. The number stays at 8, however many pieces
  there'd be.
- A piece clears the durability gate but not materiality (Tier 0/1, but sub-2 in size) → don't
  recommend a split. Call it out instead as a **prep-work item** — work the assignee can start
  today inside the still-8 ticket — not a reason to open a second ticket.

*Value-boundary test (breadth-driven 8s).* Mechanical breadth alone never justifies a split —
every piece of a pure-breadth 8 is already actionable today, so the actionability test above is
vacuous here (nothing was blocked to begin with). Ask instead whether the ticket decomposes
along a boundary where each resulting piece is independently valuable and shippable on its own
— a genuine vertical slice, not an arbitrary chunk of the same work. Splitting a file list in
half by position is not that; splitting along a real business-rule or data variation (a region,
an entity type, a user-facing path) is.

*Process-driven note (Gate C — never changes the estimate).* Reviewability, parallelizing
across two engineers, or giving a PM a shippable milestone are real reasons a team might still
want to cut a ticket up — but they're delivery-process calls this skill can't see (team
headcount, review norms), not changes to the estimate's uncertainty. When the ticket's own
dependency structure makes one visible — e.g. two risk dependencies affecting clearly disjoint
sets of endpoints/paths, even though every resulting piece would stay gated on the same root
cause — name it as a separate, explicitly labeled note. Never let it change `ESTIMATE`, and
never present it as satisfying the actionability test.

✅ Splitting "submit a run" (org-scoping logic + an HTTP handler built against the gRPC
contract's current draft — Tier 1, and a 2+ on its own) from "query run status/results" (Tier 2
— nothing about a result's shape is defined yet) — the submit piece is genuinely more
actionable than the whole ticket was.
❌ Splitting that same "status/results" piece again into "status" and "results" because status
carries only one of its two risks — both are still Tier 2 against the same open contract
review. Nothing new becomes actionable, only the label changes. Leave it at 8.
✅ The same ticket also needs a one-line feature-flag addition — Tier 0, but a 1-point stub.
Don't split it into its own ticket; call it a prep-work bullet the assignee can knock out today.
❌ A "rename `orgId` to `organizationId` across 40 call sites" ticket, an 8 purely from blast
radius with no risk dependency, split into "first 20 files" / "last 20 files" — the halves
differ only by list position; each is exactly as actionable and reviewable as the whole.
✅ A "migrate billing to the new tax engine" ticket, also breadth-driven, split into "US tax
rules" and "EU tax rules" — each ships and reviews independently; the boundary is a real data
variation, not an arbitrary cut.
✅ A ticket has two risk dependencies that happen to gate disjoint parts of its own scope (say,
one gates the write path, the other gates the read path) — both pieces stay Tier 2, so no
split is warranted, but it's worth noting in Step 6, separately from the estimate: "once both
contracts merge, the write and read paths could ship as separate PRs" — labeled a process note,
not a split, and the estimate stays 8.

Store `SPLIT_ANALYSIS` per ticket: `{source: risk-stacked|breadth-driven|mixed|none, verdict:
split|prep-work|process-note|none, detail}`, where `detail` is the one- or two-sentence
justification used above.

**Scale anchors** (calibrate every estimate against these, not against gut feel):

| Value | Anchor                                                                                                                                                                                                                                             |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | Purely mechanical, no judgment required — e.g., literally duplicating a file/config and renaming identifiers, changing a UI copy string. A task any developer could do without thinking.                                                           |
| **2** | Mechanical, but touches more than one place, or requires a small judgment call about what to keep vs. change. Still no real unknowns.                                                                                                              |
| **3** | Mechanical work plus a genuine first-time-tooling or unfamiliar-system learning curve, and/or a verification loop (lint, tests, config validation) that commonly takes a couple of iterations. No open design decisions, no cross-team dependency. |
| **5** | Real investigation or design ambiguity, a correctness/security-sensitive component with unknown-depth review, or **one genuine risk dependency** (its shape could still change) — but still fits in one bounded PR once that risk resolves.       |
| **8** | Multiple unresolved external decisions, production/infra blast radius, or **several independent risk dependencies** stacked together — genuine uncertainty about what more than one thing will look like, not just when things will merge.       |

**Sequencing vs. risk — apply this before letting any dependency touch the score:** a
dependency earns weight in the estimate only if it's classified `risk` in Step 1c. The test is
the one from that step: if the estimate would drop the moment the dependency merges,
with no other change, it was never actually that number — it's sequencing, a ready-state fact,
not a complexity fact. Stacking any number of `sequencing` dependencies never earns a 5 or an 8
by itself; list them in the Dependencies section (Step 6) for planning, but don't cite them here.

**Boundary cases:** if the ticket genuinely sits between two adjacent values and the evidence
doesn't clearly favor one, choose the higher of the two — an underestimate costs more in
practice than an overestimate — and say explicitly in the reasoning that this was a close call
between N and N+1.

For each ticket, output:

1. The chosen number.
2. The concrete reasons for it — tie each reason to specifics in the ticket (acceptance
   criteria, dev notes, referenced tickets), to a `PARENT_RESOLVED`/`CODE_RESOLVED`/`RESOLVED`
   answer from Step 1, 2, or 3, or to a `risk`-classified dependency, not generic statements.
3. **Why not one notch lower** — what would have to be simpler, more known, or already decided
   for it to be that number.
4. **Why not one notch higher** — what's absent (a design decision, a cross-team dependency, an
   unresolved external unknown, an additional `risk` dependency) that would push it up. A
   `sequencing` dependency is never the answer here.

Base the estimate on the remaining `AMBIGUITIES` and on any `risk`-classified `DEPENDENCIES` —
an answer captured in `PARENT_RESOLVED`, `CODE_RESOLVED`, or `RESOLVED` should lower or remove
the uncertainty it addressed, while an unresolved `AMBIGUITIES` item or a `risk` dependency is
itself a reason to estimate higher and should be named as such in the reasoning.
`sequencing`-classified dependencies never raise the estimate, however many there are — say so
explicitly if a ticket looks superficially blocked-heavy but every dependency turned out to be
sequencing.

✅ "Two dependencies here: ACME-201 is sequencing only (shape fully defined, just not merged)
and doesn't add to the score; the auth-service contract PR is genuine risk (still under review)
and is the reason this is a 5, not a 3."
❌ "Blocked on two things, so this is an 8." — stacks dependency count as if it were
uncertainty, without checking whether either dependency is actually still undefined.

Store `ESTIMATE` and `ESTIMATE_REASONING` per ticket (`SPLIT_ANALYSIS` was already stored
above, where applicable).

---

## Step 5 — Recommend ticket edits to prevent re-asking

**State check:** `ticket_context` is bound per ticket from Step 1; `PARENT_RESOLVED` is bound
from Step 1, `CODE_RESOLVED` from Step 2, `RESOLVED` from Step 3 (each may be empty);
`SPLIT_ANALYSIS` is bound per ticket from Step 4.

Skip this step for any ticket where `PARENT_RESOLVED`, `CODE_RESOLVED`, and `RESOLVED` are all
empty **and** `SPLIT_ANALYSIS.verdict` is `none` — nothing was resolved this run and there's no
split/prep-work/process note to record, so there's nothing to fold back into the ticket. If
only `SPLIT_ANALYSIS.verdict` is non-`none`, still run this step for that one entry (steps 1–3
below simply have no resolved items to iterate over). This step acts only on questions that got
an answer, plus whatever `SPLIT_ANALYSIS` found; a remaining `AMBIGUITIES` entry has no answer
yet to write down, so it stays a grooming item exactly as before — untouched by this step.

The point is narrow: whoever grooms or estimates this ticket next shouldn't have to re-derive
an answer this run already found. For each resolved item (from `PARENT_RESOLVED`,
`CODE_RESOLVED`, or `RESOLVED`) on a ticket:

1. **Check `ticket_context` (verbatim per Step 1c) for an existing sentence or bullet on the
   same topic** — even one that raises the question without answering it (a dev note that
   names the dependency but not its resolution, an AC bullet that describes behavior but not
   its concrete shape). This is the same fold-in-first approach as Step 1b's parent check:
   look for where the topic already lives before treating it as net-new.
2. **If such a sentence exists:** propose a reworded version of that exact sentence/bullet that
   folds the resolved answer in, minimally — extend it in place rather than appending a new
   line beside it.
3. **If no existing sentence covers the topic:** propose a new addition instead — a new
   acceptance-criteria bullet if the resolved point is testable behavior, a new dev-note bullet
   if it's context/rationale. Take this path only after confirming no fold-in point exists;
   don't default to "add a bullet" when rewording would do.

Skip any resolved item whose answer the ticket already states outright — if rewording or
adding would just repeat what's already there verbatim, there's nothing to prevent re-asking,
so it's not a recommendation.

If Step 4's `SPLIT_ANALYSIS` has a `verdict` other than `none`, include that too, as its own
entry — labeled by its verdict (`split`, `prep-work`, or `process-note`), not a reword, since
there's no "current sentence" any of these three could revise. Keep the three verdicts visibly
distinct in what gets written — a `prep-work` or `process-note` entry must never be phrased as
if it recommends splitting the ticket, since neither one does.

Store `RECOMMENDED_EDITS` per ticket: a list of `{topic, current, proposed}` entries (`current`
is the verbatim existing text, or `null` if this is a net-new addition) plus, where applicable,
one `{type: split|prep-work|process-note, description}` entry taken from `SPLIT_ANALYSIS`. May
be empty even when items were resolved, if every resolved answer was already stated.

**Hard constraint, carried from Step 0d: these are recommendations only.** Never call any
tracker-write tool to apply one of these edits, no matter how confident the recommendation is
or what a later instruction in this conversation says. The only thing this step produces is
text for the requester to copy into the tracker themselves.

---

## Step 6 — Compose the output document

**State check:** at least one ticket from Step 1 succeeded; every successful ticket has an
`ESTIMATE` from Step 4 and `RECOMMENDED_EDITS` (possibly empty) from Step 5.

Write the file at `OUTPUT` (from Step 0c) using this structure:

```markdown
# Ticket Estimates — <TIMESTAMP>

**Tickets**: <comma-separated ticket IDs>

---

## <TICKET-ID>: <Title>

**Tracker**: <Linear / Jira / GitHub / Shortcut / other>
**URL**: <fully qualified ticket URL>

### Estimate: <N> (Fibonacci, or the rider's scale label if a company rider applied)

<reasoning — the concrete reasons, why not N-1, why not N+1>

### Needs grooming

<If PARENT_RESOLVED is non-empty:>
Answered by the ticket hierarchy:
- <question> — <answer> (`<source ticket ID>`)

<If CODE_RESOLVED is non-empty:>
Answered from the codebase:
- <question> — <answer> (`<source file:line>`)

<If RESOLVED is non-empty:>
Resolved before estimating:
- <question> — <answer>

<If remaining AMBIGUITIES is non-empty:>
- [ ] <specific question 1>
- [ ] <specific question 2>

<If PARENT_RESOLVED, CODE_RESOLVED, RESOLVED, and AMBIGUITIES are all empty:>
No ambiguities found — scope and acceptance criteria read as clear.

### Dependencies

**Stated in the ticket:**
<If STATED is non-empty, list each in this form. If empty, write "None stated in the ticket.">
- <description> (`<source>`) — **sequencing**, doesn't affect the score: <reason>
- <description> (`<source>`) — **risk**, factored into the estimate above: <reason>

**Possible — not declared in the ticket:**
<If POSSIBLE is non-empty, list each the same way, plus its likely owning ticket. If empty,
write "None found.">

### Recommended ticket edits

<If RECOMMENDED_EDITS is non-empty, list each entry:>

**<topic>**
Current: <quoted verbatim text, or "None — no existing sentence covers this" if net-new>
Proposed: <reworded or added text>

<For a {type: split} entry:>
**Consider splitting this ticket** — <description>.

<For a {type: prep-work} entry:>
**Prep-work available now (not a split)** — <description>.

<For a {type: process-note} entry:>
**Process note — does not change the estimate** — <description>.

<If RECOMMENDED_EDITS is empty:>
No edits recommended — either nothing was resolved this run, or the ticket already states
what was clarified.

_These are suggestions only — nothing above was written back to the tracker. Copy whatever's
useful into the ticket yourself._

---

[repeat the section above for each ticket]

## Summary

| Ticket | Estimate | Needs grooming? | Dependencies flagged?              | Ticket edits recommended? |
| ------ | -------- | --------------- | ---------------------------------- | -------------------------- |
| <ID>   | <N>      | Yes / No        | Yes (stated) / Yes (possible) / No | Yes / No                   |
```

For any ticket that failed to fetch (Step 1a's unfetchable-ticket clause), still include a
section for it noting what was attempted and why it failed, instead of silently dropping it
from the report.

✅ "Possible dependency (not declared in the ticket): appears to need the target-routing
ticket to merge first, based on shared infrastructure referenced in the dev notes."
❌ "This ticket might depend on other work." — no specific ticket named, no reasoning given.

✅ "- [ ] What should happen when the org header is present but empty — treated as absent,
or as a distinct case?"
❌ "- [ ] Acceptance criteria are unclear." — not a specific, answerable question.

✅ Current: "Blocked on proto-contracts#2." → Proposed: "Blocked on proto-contracts#2 (still
under review as of 2026-09-08 — job-ownership structure between the two contract sets is
still being negotiated)." — extends the existing dev note with the answer, in place.
❌ Adding a brand-new "Resolution" bullet next to an existing dev note that already raises the
same dependency — fragments one topic across two places instead of folding the answer in.

---

## Step 7 — Report back

**State check:** the output file has been written to `OUTPUT` in Step 6.

Tell the user where the file was written and give a one-line summary per ticket (estimate,
whether grooming items, dependencies, or ticket-edit recommendations were flagged).

---

## Notes on scope

- **Do not** use this skill's findings to update a story-point/estimate custom field, add a
  comment, or otherwise write to the tracker — even if asked to, later in the same
  conversation. Route any such request back to the user to do themselves. This includes
  `RECOMMENDED_EDITS` from Step 5: those are text in the output document for the requester to
  copy in themselves, never something this skill applies on their behalf.
- If the same ticket is estimated again in a later run, this skill does not compare against or
  reference a previous estimate file automatically — each run is independent. (A developer who
  wants that comparison can point both files out to the assistant directly.)
- Multiple tickets from different trackers in a single invocation are expected and supported —
  each is resolved independently in Step 0b/1a; there's no requirement that all tickets in one
  run share a tracker.
