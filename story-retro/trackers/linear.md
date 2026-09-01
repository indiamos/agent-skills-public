# Tracker: Linear

Uses the `mcp__plugin_linear_linear__*` tools (`list_issues`, `get_issue`).

## Build the query

Linear has no single query-string DSL equivalent to JQL — translate `INPUT` into a `list_issues`
parameter set instead, then present the resolved parameters to the user for approval (per
`SKILL.md`'s Step 0), e.g. `assignee: me, state: Done, updatedAt: -6M`.

1. If INPUT is absent, construct this default: `{assignee: "me", updatedAt: "-6M", orderBy: "updatedAt"}`
   (see "Fetch the ticket list" below for how "Done" is determined — it isn't a `list_issues`
   filter here).
2. If INPUT is one or more ticket IDs (e.g. `STRIDE-18`), fetch each directly with `get_issue` —
   skip `list_issues` entirely for this case.
3. If INPUT is natural language, translate it to parameters. Examples:
   - "STRIDE-885 and higher" → no native range filter; fetch broadly (e.g. by assignee/team) and
     filter client-side by comparing the numeric suffix of each returned `id`.
   - "all STRIDE tickets since 2025-11-13" → `{team: "STRIDE", updatedAt: "2025-11-13"}`
   - "my tickets from last sprint" → first call `list_cycles({teamId, type: "previous"})` to
     resolve the actual cycle, then `list_issues({assignee: "me", cycle: <resolved cycle id>})`
   - "my tickets from this project" → `{project: "<project name>", assignee: "me"}`
4. If INPUT already looks like a `list_issues` parameter set the user typed directly (e.g.
   pasted from a previous run), use it as-is.

## Fetch the ticket list

Call `list_issues` with the resolved parameters. Request only `id` in `fields` — `id` is always
returned and is Linear's human-readable identifier (e.g. `STRIDE-18`), which is all the parent
needs to build the dispatch list.

**Linear's state names are workflow-configurable per team** (a "Done" column might be named
something else on some teams), so don't filter on `state: "Done"` as the sole completion signal.
Fetch broadly by assignee/team/date range, then treat a ticket as done only once `get_issue` is
called on it in Step 3a and its `completedAt` field is non-null — mirroring Jira's
`statusCategory = Done` category-based check rather than a literal status-name match. Skip (and
note in the aggregate summary) any fetched ticket whose `completedAt` is null.

## Fetch full ticket data

Call `get_issue({id})`. This alone is dense enough to skip a separate fields-limited fallback —
it returns `description`, `status`, `statusType`, `stateHistory`, `attachments`, `assignee`,
`createdBy`, `project`, and `parentId` in one call.

**`stateHistory`** (array of `{state: {name, type}, startedAt, endedAt}`) is Linear's changelog
equivalent for status transitions — use it directly for Step 4's timeline computation
(`In Progress` → `In Review` → `Done`, and to detect a premature-Done-then-reopened cycle: look
for a completed state followed by a non-completed one later in the array).

Linear does not expose field-level edit history for the description text through this MCP (no
changelog-style "who edited the description and when"). Omit the report's **Description
editors** line for Linear tickets — `SKILL.md` already allows omitting it when there's nothing
to report.

## Find linked PRs

`get_issue`'s `attachments[]` array includes any GitHub PR Linear has automatically linked to
the issue (via its GitHub integration) — each entry has `title` (the PR title) and `url`. Filter
to entries whose `url` contains `github.com` and `/pull/`; these are Linear's proactive-link
equivalent of Jira's development panel. Count these as "native tracker link" matches (Method A)
in `SKILL.md`'s Step 3b, ahead of any GitHub-side text search.

`gitBranchName` (also on `get_issue`) is useful as an extra signal for Method B's branch-name
search if the attachment-based lookup finds nothing (e.g. the PR was never opened from Linear's
suggested branch name, or the GitHub integration wasn't connected when it was opened).
