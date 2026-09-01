# Tracker: Jira

## Build the query

Translate `INPUT` into JQL, then present it to the user for approval (per `SKILL.md`'s Step 0).

1. If INPUT is absent, construct this default:

   ```
   project = XYZ AND statusCategory = Done AND assignee = currentUser() AND updated >= -6M ORDER BY updated DESC
   ```

2. If INPUT is one or more ticket IDs, construct:

   ```
   issueKey in (XYZ-1038, XYZ-1042) ORDER BY issueKey ASC
   ```

3. If INPUT is a raw JQL string (contains `=`, `AND`, `OR`, `in`, `ORDER BY`), use it as-is.
4. If INPUT is natural language, translate it to JQL. Examples:
   - "XYZ-885 and higher" → `project = XYZ AND issueKey >= XYZ-885 AND statusCategory = Done ORDER BY issueKey ASC`
   - "all XYZ tickets since 2025-11-13" → `project = XYZ AND statusCategory = Done AND updated >= "2025-11-13" ORDER BY updated DESC`
   - "my tickets from last sprint" → `project = XYZ AND statusCategory = Done AND assignee = currentUser() AND sprint in closedSprints() ORDER BY updated DESC`

## Fetch the ticket list

Use the Jira MCP to fetch the list of tickets matching the confirmed JQL. Fetch **lightweight
fields only** in this step — do NOT request description, comments, or changelog here.

Do not request any fields — the ticket key is always returned and is the only thing the parent
needs to build the dispatch list.

Use `limit: 50` per call (the MCP's maximum; the Atlassian v3 API supports 100 but the MCP caps
it at 50). **`start_at` is silently ignored for Jira Cloud** — the Atlassian MCP v3 API uses
cursor-based pagination internally, and `startAt` is hardcoded to `0` in every response. You
will always get the first 50 matching tickets. If your scope exceeds 50, narrow the JQL.

A ticket is "Done" when its `statusCategory` is `Done` (as opposed to To Do, In Progress, or In
Review).

## Fetch full ticket data

Call `jira_get_issue` with `fields: "*all"` and `expand: "changelog"`. If the response is
flagged as too large to read at once, fall back to two separate calls: one for
`fields: "summary,description,status,assignee,reporter,issuetype,comment,created,updated"` and
one for `expand: "changelog"` with minimal fields.

The changelog is Jira's native audit trail — use it directly for "what changed and when"
(status transitions, description edits, assignee changes) rather than inferring from ticket
state alone.

## Find linked PRs

Collect all PRs listed in the ticket's `development` panel (exposed via the Jira MCP as part of
the issue's development-status data, alongside branch and commit links). This is Jira's
proactive PR-linking mechanism — count these as "native tracker link" matches (Method A) in
`SKILL.md`'s Step 3b, ahead of any GitHub-side text search.
