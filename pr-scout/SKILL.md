---
name: pr-scout
description: "Use when you want a thorough code review of a PR — checking for bugs, CLAUDE.md compliance, historical context, and struct invariants. Invoke with a PR number or URL; optionally pass a file path (e.g., file:/path/to/review.md) to write the result to a file instead of posting a GitHub comment."
license: Apache-2.0
argument-hint: "PR-number-or-URL [file:output-path.md] [commits]"
---

<!--
  Derived from anthropics/claude-plugins-official (code-review command) under the Apache 2.0 License.
  Source: https://github.com/anthropics/claude-plugins-official
  Original authors: Anthropic
  Substantially modified by indiamos.
-->

## Step 0 — Bind state variables before any other action

**State check:** Read the arguments provided when the skill was invoked.

### 0★. GitHub MCP availability check + reviewer identity

Before making any `gh` CLI calls or spawning any subagents, verify that the GitHub MCP server is installed, enabled, and authenticated by calling `mcp__github__get_me`.

- If the call **succeeds**: store `login` from the response as `REVIEWER`. GitHub MCP is available and authenticated. Proceed to 0b.
- If the call **fails with "tool not found", "unknown tool", or similar**: GitHub MCP is not installed or not enabled in this session.
- If the call **fails with an authentication or permission error**: GitHub MCP is installed but not authenticated.

Route based on the result of the MCP call:

- **Success** → proceed to 0b with `REVIEWER` bound.
- **Failure** → report the specific failure mode (not installed / not enabled / not authenticated) and ask:

  > ⚠️ GitHub MCP is [not installed / not enabled / not authenticated]. Without it, this skill issues dozens of `gh` CLI calls — each of which may require an SSH fingerprint prompt on your machine.
  >
  > Proceed anyway? (yes / no)

  Wait for the user's response. If **no**, halt immediately. If **yes**, fall back to:

```sh
gh api user --jq '.login'
```

Store the result as `REVIEWER`. If this also fails, report the error and halt. Then continue to 0b.

### 0b. PR reference

Extract the PR reference from arguments (PR number, URL, or `owner/repo#number`). If no PR reference is present, ask the user: "Which PR should I review? Please provide a PR number, URL, or owner/repo#number." Wait for their response before continuing.

Store the normalized reference as `PR_REF`.

Also capture any free-text context the user provided alongside the PR reference (e.g., "this is a re-review", "the author addressed my comment about X"). Store as `REVIEWER_CONTEXT` (may be empty). Pass this to all specialist agents — it can guide their focus and prevent redundant flagging of already-addressed concerns.

### 0c. PR author

Call `mcp__github__pull_request_read` with the owner, repo, and PR number derived from `PR_REF`. Extract the author login from the response.

Store the result as `PR_AUTHOR`. If the MCP call fails, fall back to:

```sh
gh pr view <PR_REF> --json author --jq '.author.login'
```

If both fail, report the error and halt.

Set `IS_AUTHOR = (REVIEWER == PR_AUTHOR)`.

### 0d. Output mode

Run:
date +%Y-%m-%d-%H%M

Store the result as `TIMESTAMP`. If the command fails or returns empty output, use only the date component (from `currentDate` in context, formatted `YYYY-MM-DD`) and omit the time suffix — do not halt. This value must be set before the prompt below.

Extract the PR number from `PR_REF` by taking the numeric portion only (e.g., from `my-github-org/advisor#576` or `576`, extract `576`). Store as `PR_NUMBER`.

Read the following files in order using the Read tool. For `PR_SCOUT_OUTPUT_DIR`, the last file that defines it wins. Do not use `echo` or any Bash command — env vars are not reliably injected into skill context.

1. `~/.claude/settings.json` (user-level) — if it exists and its `env` object contains `PR_SCOUT_OUTPUT_DIR`, store that value as `OUTPUT_DIR`; otherwise set `OUTPUT_DIR` to empty string. If it contains `PR_SCOUT_DEFAULT_OUTPUT`, store that value as `DEFAULT_OUTPUT_MODE`; otherwise set `DEFAULT_OUTPUT_MODE` to empty string.
2. `.claude/settings.json` relative to CWD (project-level) — if it exists and its `env` object contains `PR_SCOUT_OUTPUT_DIR`, its value overrides the user-level one. If it contains `PR_SCOUT_DEFAULT_OUTPUT`, its value overrides the user-level one.
3. `.claude/settings.local.json` relative to CWD (project-local) — if it exists and its `env` object contains `PR_SCOUT_OUTPUT_DIR`, its value overrides both. If it contains `PR_SCOUT_DEFAULT_OUTPUT`, its value overrides both.

Compute `DEFAULT_OUTPUT_PATH`:

- If `OUTPUT_DIR` is non-empty: `$OUTPUT_DIR/$TIMESTAMP-pr-$PR_NUMBER-review.md`
- Otherwise: run `pwd` to get `CWD`; use `$CWD/$TIMESTAMP-pr-$PR_NUMBER-review.md`

Users can set the global default in `~/.claude/settings.json` under `env`, or a per-repo override in `.claude/settings.local.json` under `env`:

```json
{
  "env": {
    "PR_SCOUT_OUTPUT_DIR": "~/ai-reviews"
  }
}
```

Bind `OUTPUT` using the first matching rule below:

1. **Explicit arg — file**: If arguments include a token matching `file:<path>` or a path ending in `.md`, set `OUTPUT = file:<path>`. Skip to 0e.
2. **Explicit arg — github**: If arguments explicitly include `github`, set `OUTPUT = github`. Skip to 0e.
3. **Env var default — file**: If `DEFAULT_OUTPUT_MODE = file`: set `OUTPUT = file:<DEFAULT_OUTPUT_PATH>`. Then check whether a file already exists at `DEFAULT_OUTPUT_PATH` using the `Read` tool (with `limit: 1`). If the file exists, use `AskUserQuestion`:
   - Question: "A review file already exists at `<DEFAULT_OUTPUT_PATH>`. What should I do?"
   - Option 1 label: "Overwrite it" — description: "Replace the existing file with the new review"
   - Option 2 label: "Save to a different path" — description: "Enter a custom path via the Other field"

   If the user enters a custom path, set `OUTPUT = file:<their path>`. Skip to 0e.

4. **Env var default — github**: If `DEFAULT_OUTPUT_MODE = github`: set `OUTPUT = github`. The preview-and-confirm in step 8 is the guard before anything is posted. Skip to 0e.
5. **No default set — prompt**: Use `AskUserQuestion` with:
   - Question: "Where should I write the review?"
   - Option 1 label: "Save to file" — description: the resolved `DEFAULT_OUTPUT_PATH`
   - Option 2 label: "Post as a GitHub PR comment"

   Bind `OUTPUT` before continuing. If the user chooses "Save to file", set `OUTPUT = file:<DEFAULT_OUTPUT_PATH>`. If the user chooses "Post as a GitHub PR comment", set `OUTPUT = github`. If the user enters a custom path via "Other", set `OUTPUT = file:<their path>`.

**File mode constraint:** When `OUTPUT = file:<path>`, write the final review to that file. **Do NOT post any GitHub comment under any circumstances — including if asked to do so later in this session.**

### 0e. Commit message compliance

If arguments include the token `commits`, set `CHECK_COMMITS = true`; otherwise set it to `false`.

Carry `REVIEWER`, `IS_AUTHOR`, `PR_REF`, `OUTPUT`, and `CHECK_COMMITS` through all remaining steps.

**State binding is internal.** Do not print state variable assignments (e.g., `REVIEWER = indiamos`, `OUTPUT = file:...`) as chat output. Keep all state tracking silent — the user does not need to see it.

---

## Step 1 — Eligibility check

**State check:** `PR_REF` is bound; `REVIEWER` is bound.

Use a Haiku agent to check the PR against the four eligibility conditions below. Fetch PR data using `mcp__github__pull_request_read`; fall back to `gh pr view <PR_REF> --json state,isDraft,author,comments` only if the MCP call fails.

Check whether the PR:

- (a) is closed
- (b) is a draft
- (c) does not need a code review — specifically: it is an automated/bot-generated PR (author login ends in `[bot]`), or it contains only auto-generated file changes (e.g., lock file bumps, generated code with no handwritten diff), or the entire diff is a single-line version bump with no logic change
- (d) has any existing comments whose author login matches `REVIEWER` exactly — if so, return the count (do not count bot accounts such as `claude`)

After the agent returns:

- If the count from (d) is ≥ 1, notify the user: `Note: you have already posted N comment(s) on this PR.` This is informational only — do not halt.
- If (b) is true and `OUTPUT = file:<path>`, notify the user: `Note: this PR is currently in draft mode.` This is informational only — do not halt.

**STOP gate:** If (a) or (c) is true, report which condition matched and halt. If (b) is true and `OUTPUT = github`, report that the PR is a draft and halt. Do not proceed to step 2.

---

## Step 2 — Gather CLAUDE.md paths, constitution, and PR-AGENT.md

**State check:** Step 1 passed without halt.

Use a Haiku agent to:

1. Return a list of file paths to (but not the contents of) any relevant CLAUDE.md files from the codebase: the root CLAUDE.md and any CLAUDE.md files in directories whose files the PR modified. To confirm each candidate path exists: call `mcp__github__get_file_contents` first; if it returns a 404 or not-found error, fall back to checking via the `Read` tool on the local filesystem. Include a path only if at least one check confirms the file exists. Store as `CLAUDE_MD_PATHS`.
2. Check whether `.specify/memory/constitution.md` exists in the repo root. If it does, store its path as `CONSTITUTION_PATH`. If it does not exist, set `CONSTITUTION_PATH = null`.
3. Check whether `PR-AGENT.md` exists in the repo root. If it does, store its path as `PR_AGENT_PATH`. If it does not exist, set `PR_AGENT_PATH = null`.

**STOP gate:** If the agent fails due to a repo access error, report the error and halt.

After the agent returns, call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 3 — PR summary and commit SHA

**State check:** `CLAUDE_MD_PATHS`, `CONSTITUTION_PATH`, and `PR_AGENT_PATH` are available.

Use a Haiku agent to:

1. View the PR and return a brief summary of the change. Store as `PR_SUMMARY`.
2. Return the full 40-character commit SHA of the PR head: call `mcp__github__pull_request_read` and extract `headRefOid` from the response. If the MCP call fails, fall back to `gh pr view <PR_REF> --repo <OWNER/REPO> --json headRefOid --jq '.headRefOid'`. Store as `COMMIT_SHA`.

**STOP gate:** If the agent fails or returns an empty summary, report the error and halt. Do not proceed to step 4 without a valid `PR_SUMMARY` and `COMMIT_SHA`.

After the agent returns, call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 4 — Six parallel specialist agents

**State check:** `PR_SUMMARY` and `COMMIT_SHA` are available.

**Commit messages:** If `CHECK_COMMITS = false`, instruct all six agents to skip commit message style issues entirely — do not flag them and do not score them. When checking commit subject line length, count the raw string only — do not include surrounding backtick or quote characters used to format the string in the report.

**Link format:** Pass `COMMIT_SHA`, `OWNER`, and `REPO` to every agent. Each agent must include a fully-formed GitHub link with every issue it returns, using line numbers identified while the file is already in context — do not leave link construction for later, because a follow-up fetch wastes tokens and risks incorrect line numbers once the file is out of context. Use the format from Appendix A: `https://github.com/OWNER/REPO/blob/COMMIT_SHA/path/to/file#L10-L14`. If a line number cannot be determined, link to the file without a range rather than omitting the link.

> ⚡ **PARALLEL LAUNCH — send all 6 Task tool calls in a single message, each with `model: "sonnet"`.**
>
> All six agents are independent. There are no dependencies between them. Do not launch any agent before the others; do not wait for one to finish before starting the next. Make all 6 Task tool calls simultaneously in one response.
>
> If you intend to call multiple tools and there are no dependencies between the tool calls, make all of the independent tool calls in parallel. Maximize use of parallel tool calls to increase speed and efficiency.

Each agent independently reviews the PR and returns a list of issues with the reason each was flagged (e.g., CLAUDE.md adherence, bug, historical context, etc.).

**GitHub data access — MCP first:** All agents must use the GitHub MCP tools for any GitHub read operation — do NOT use `gh` CLI unless the MCP call explicitly fails. To fetch the PR diff and file changes, call `mcp__github__pull_request_read`. To read individual file contents at a specific commit, use `mcp__github__get_file_contents`. To search previous PRs, use `mcp__github__search_pull_requests`. Fall back to `gh pr diff`, `gh pr view`, or `gh search` only if the MCP call returns an error.

**No Bash tool in specialist agents — include this constraint verbatim in every agent prompt:**

> **CRITICAL — NO BASH TOOL.** Do not use the Bash tool for any purpose. Every Bash call requires a manual user-approval prompt and will block or abort the review. This means:
>
> - No `cat`, `grep`, `find`, `head`, `tail`, `sed`, or any shell command
> - No `gh pr diff`, `gh pr view`, `gh pr show`, `git log`, `git blame`
> - No inline Python or shell pipelines
>
> Read GitHub file contents with `mcp__github__get_file_contents`. Read the PR diff with `mcp__github__get_pull_request_files`. Search with `mcp__github__search_issues` or `mcp__github__search_code`. Read local files with the `Read` tool; search local files with the `Grep` tool.

**Verify before flagging — include this constraint verbatim in every agent prompt:**

> **CRITICAL — VERIFY BEFORE FLAGGING.** Before raising a concern as an issue, check whether the answer is already present in the files you have read. Do not generate questions whose answers are visible in the diff or in file contents already in context. If you can answer your own question by reading the provided code, do so — and either confirm the concern is real or drop it. If you are about to write "could", "might", "possible", or "it appears" in an issue description, treat this as a signal that you have not finished verifying: check the relevant code before flagging. Use conditional language only when the code is genuinely inaccessible (an external service, a closed-source library, or runtime-only behavior). An unverified hypothetical wastes reviewer time on a non-issue — it is worse than no finding.

| Agent                                                     | Focus                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Instructions                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --- |
| **Agent 1** — CLAUDE.md, constitution & PR-AGENT.md audit | Compliance with `CLAUDE_MD_PATHS`. Note: CLAUDE.md is guidance for Claude while writing code; not all instructions apply during code review. If `CONSTITUTION_PATH` is non-null, also audit for compliance with the constitution at that path. The constitution describes architectural principles, design constraints, and team conventions that should be respected by all code changes. If `PR_AGENT_PATH` is non-null, also audit for compliance with the criteria in that file. PR-AGENT.md contains repo-specific PR review criteria.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | When returning any CLAUDE.md, constitution, or PR-AGENT.md violation, quote the relevant rule verbatim in the issue description — scoring agents will not re-read those files.                                                                                                                                                                                                                                                                                                                                                                                     |
| **Agent 2** — Bug scan                                    | Read the file changes in the PR using `mcp__github__pull_request_read`, then do a shallow scan for obvious bugs. Focus primarily on the diff. For function calls in the diff that are defined in this codebase (not stdlib or vendor), read enough of the definition to understand the **full return contract of every return value** — not just the error — and verify the caller correctly handles all meaningful non-error states. For calls to internal packages (scoped to the organization, e.g., `@my-github-org/*`): before flagging a return-type or behavioral concern, check whether the package source is accessible: look in `node_modules/<package>/`, search for a matching repo in `~/repos/`, or search the org's repositories on GitHub via MCP. If the source is found, read the relevant method definition and verify the concern before reporting it. Flag the return type as "unverified" only if the source genuinely cannot be located. Also explicitly scan for any loop body that calls a method on a repository, database, external client, or service object; flag these as potential N+1 patterns regardless of loop size. Also check whether any guard meant to enforce a security or authorization decision silently no-ops when its input is missing or unset, instead of failing closed — e.g., a null/absent config value, permission, or feature flag that should block a request but is instead treated as "no restriction"; flag fail-open behavior on missing required input as a bug, in any language or framework. If the diff adds or changes authentication/authorization on an HTTP route, verify that the route's OPTIONS/preflight handling (or other non-primary request path, e.g. HEAD, a health check) wasn't broken by the new gate. Flag large bugs; ignore small issues and nitpicks. Ignore likely false positives. | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Agent 3** — Git history                                 | Read the git blame and history of the modified code. Identify bugs that become apparent only in that historical context.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Agent 4** — Previous PR comments                        | (1) Find previous PRs that touched these files using `mcp__github__search_pull_requests` (search by file path or by the same filenames). For each found PR, fetch its review comments using `mcp__github__pull_request_read`. Check whether comments from those reviews also apply to the current PR. (2) Check the **current PR** for bot comments by reading the `comments` already returned in the `pull_request_read` response (do not re-fetch); filter for any commenter whose login ends in `[bot]`. (3) For bot comment node ID lookup and edit history, use `gh api` — no MCP equivalent exists for GraphQL edit history: get comment node IDs with `gh api repos/OWNER/REPO/issues/PR_NUM/comments --jq '.[]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | {id: .node_id, user: .user.login}'`, then fetch edits with `gh api graphql -f query='{ node(id: "NODE_ID") { ... on IssueComment { userContentEdits(last: 10) { nodes { editedAt diff } } } } }'`. For all other GitHub read operations in this agent, use MCP tools. If a comment has been edited and the diff shows content was removed or replaced, return it as an issue: "Bot comment edited after posting — original content included: [excerpt from the removed diff]." If the comment has no edit history or was only corrected for typos, do not flag it. | —   |
| **Agent 5** — Code comments                               | Read code comments in the modified files. Verify the PR's changes comply with any guidance in those comments.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Agent 6** — Code-path & struct invariants               | For each function with lines modified by this PR: (1) read the complete function body; (2) enumerate every return path — for any guard, flag, variable, or data structure introduced or changed by this PR, check whether each early-return path handles it consistently with the main path, and flag early returns that were not updated but should have been; (3) for each struct constructed and returned in the modified function, state the expected invariants between fields (e.g., `TotalCount == len(Items)`) and verify those invariants hold at every return site.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

**STOP gate:** Collect all results. If all six agents returned errors, report and halt. If some failed, proceed with results from the agents that succeeded and note which agents failed.

Store the combined issue list as `ALL_ISSUES`. Then call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 4.5 — Hypothetical framing gate

**State check:** `ALL_ISSUES` is collected. If empty, skip to step 5.

Scan every issue in `ALL_ISSUES` for conditional language: "could", "might", "possible", "possibly", "potentially", "may result in", "it appears", "unclear whether", "if [condition] holds", "depending on". This is a literal string match — if any of these phrases appear in the issue description, the issue is flagged for verification.

If no issues are flagged, proceed to step 5 immediately.

For each flagged issue, dispatch a verification agent. All flagged issues are independent — launch all verification agents in a single parallel batch.

> ⚡ **PARALLEL LAUNCH — send all verification Task tool calls in a single message, each with `model: "sonnet"`.**

Each verification agent receives:

- The issue description
- The file path(s) and line numbers referenced in the issue
- `COMMIT_SHA`, `OWNER`, `REPO`

Each verification agent must:

1. Read the relevant code using `mcp__github__get_file_contents` — do not skip this step, because the issue description alone is insufficient to reach a verdict.
2. Return exactly one of:
   - `CONFIRMED: <reworded issue description with conditional language removed and evidence cited>` — the concern is real based on the code
   - `DROPPED: <one-sentence reason>` — the code shows the condition cannot occur, or the concern is unfounded

**No Bash tool** — same constraint as specialist agents in step 4.

After all verification agents return:

- Replace each flagged issue in `ALL_ISSUES` with the agent's result:
  - `CONFIRMED` → replace the original description with the reworded one
  - `DROPPED` → remove the issue from `ALL_ISSUES` entirely
- Unflagged issues pass through unchanged.

Then call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 5 — Score all issues

**State check:** `ALL_ISSUES` is collected (may be empty).

If `ALL_ISSUES` is empty, skip to step 6 with an empty scored list.

Otherwise: for **every** issue in `ALL_ISSUES` — **without pre-filtering or manual curation** — launch a parallel agent with `model: "haiku"`. The scoring agent is the filter; do not reduce the list before this step.

> ⚡ **PARALLEL LAUNCH — send all scoring Task tool calls in a single message.**
>
> All scoring agents are independent. Make all Task tool calls simultaneously in one response. Do not wait for any scoring agent to finish before launching the others.
>
> If you intend to call multiple tools and there are no dependencies between the tool calls, make all of the independent tool calls in parallel. Maximize use of parallel tool calls to increase speed and efficiency.

**Non-empty guard:** Before launching each scoring agent, verify the issue has a non-empty description. Skip any issue with a blank or whitespace-only description rather than passing it to an agent — an empty content block will cause an API error.

Each scoring agent receives:

- `PR_REF`
- The issue description and the agent that raised it
- `CLAUDE_MD_PATHS`
- `CONSTITUTION_PATH` (may be null)
- `PR_AGENT_PATH` (may be null)

**Scoring agents must call no tools — return a score and rationale immediately.** Score based solely on the issue description and evidence provided in the prompt. If you cannot verify a claim from the information given, assign 25 — do not read files, run shell commands, or do additional research — because every tool call by a scoring agent requires a user approval, and the 25-point tier exists precisely for unverifiable cases.

**Hypothetical framing check:** If the issue description uses conditional language ("could", "might", "possible", "it appears", "may result in"), check whether the relevant code was accessible to the specialist agent (same repo, files that agent reviewed). If the code was accessible and checking it would confirm or deny the concern, cap the score at 25 — the specialist agent was required to verify before flagging. If the code was genuinely inaccessible (external service, closed-source dependency, runtime-only behavior), score normally.

For CLAUDE.md, constitution, or PR-AGENT.md issues: if the issuing specialist agent quoted the relevant rule verbatim in the issue description, treat that as verified and score accordingly. If no rule is quoted, score at most 25.

Each scoring agent returns a confidence score 0–100. Provide this rubric verbatim:

> - **0** — Not confident at all. This is a false positive that does not stand up to light scrutiny, or is a pre-existing issue.
> - **25** — Somewhat confident. Might be a real issue, but may also be a false positive. Unable to verify. If stylistic, it is not explicitly called out in the relevant CLAUDE.md.
> - **50** — Moderately confident. Verified as real, but might be a nitpick or rare in practice. Not very important relative to the rest of the PR.
> - **75** — Highly confident. Double-checked, very likely real, will be hit in practice. The existing approach is insufficient. Very important, or directly mentioned in the relevant CLAUDE.md.
> - **100** — Absolutely certain. Confirmed real, will happen frequently. Evidence directly confirms it.

For CLAUDE.md-flagged issues: the agent must double-check that the CLAUDE.md actually calls out that specific issue before scoring above 50.

For constitution-flagged issues: the agent must double-check that the constitution at `CONSTITUTION_PATH` actually calls out that specific issue before scoring above 50. If `CONSTITUTION_PATH` is null, skip this check.

For PR-AGENT.md-flagged issues: the agent must double-check that the file at `PR_AGENT_PATH` actually calls out that specific issue before scoring above 50. If `PR_AGENT_PATH` is null, skip this check.

Store the scored list as `SCORED_ISSUES`. Then call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 6 — Filter and separate commit message notes

**State check:** `SCORED_ISSUES` is available (may be empty).

### 6a. Score filter

Keep only issues with score ≥ 65. Store as `HIGH_CONFIDENCE_ISSUES`.

### 6b. Commit message style handling

If `CHECK_COMMITS = false`: remove any commit message style issues that slipped through — the user opted out of commit analysis. Do not surface them in any form. Set `COMMIT_STYLE_NOTES` to empty. Skip the rest of this sub-step.

If `CHECK_COMMITS = true`, partition `HIGH_CONFIDENCE_ISSUES`:

- Remove commit message style issues from `HIGH_CONFIDENCE_ISSUES`. Collect them separately as `COMMIT_STYLE_NOTES`. They will appear at the end of the review document under `## Commit message notes`, not in the scored issue list.

### 6c. Empty-result handling

If `HIGH_CONFIDENCE_ISSUES` is empty after filtering:

- There are **no scored issues to report** — but output must still be produced.
- If `IS_AUTHOR = true` and `COMMIT_STYLE_NOTES` is non-empty: proceed to step 7 with a "no scored issues" main body and commit notes appended.
- Otherwise: proceed to step 7 with a "no issues found" summary.
- **Do not halt.** Always produce output in this step.

---

## Step 7 — Re-check eligibility

**State check:** `HIGH_CONFIDENCE_ISSUES` and any `COMMIT_STYLE_NOTES` are ready.

Use a Haiku agent to verify the PR is still open and check whether it has been converted to draft since step 1.

**STOP gate:** If the PR is now closed, halt. If it has been converted to draft and `OUTPUT = github`, halt. If it has been converted to draft and `OUTPUT = file:<path>`, notify the user and continue.

After the agent returns, call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 7.5 — Annotate issues already raised in existing PR comments

**State check:** `HIGH_CONFIDENCE_ISSUES` is ready. If empty, skip this step.

Fetch all current review comments and issue comments on the PR by calling `mcp__github__pull_request_read` — the response includes both `reviews` and `comments`. If the MCP call fails, fall back to:

```sh
gh pr view <PR_REF> --json reviews,comments
```

For each issue in `HIGH_CONFIDENCE_ISSUES`, check whether any existing comment substantively raises the same concern. Matching is semantic, not literal — look for comments that address the same code location or the same underlying problem.

If a match is found, append a note to that issue's output entry:

> _(Already raised: [link to comment])_

Obtain the comment URL from the API response (`html_url` field). Do not @mention or name the comment author.

Store the annotated list back as `HIGH_CONFIDENCE_ISSUES`. Then call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 8 — Output

**State check:** `OUTPUT` is bound from step 0. Eligibility confirmed.

**Task completion:** After writing or posting the review, immediately call `TaskUpdate` to mark this step's task `completed` before proceeding to Step 9.

Compose the review document using the format below, then route it:

- **`OUTPUT = file:<path>`** → Write the review to `<path>`. Done. Do not post a GitHub comment.
- **`OUTPUT = github`** → Preview flow:
  1. Print the full composed review in the chat so the user can read it.
  2. Ask: "Post this comment to the PR? (yes / no)"
  3. Wait for the response.
  4. If **yes** → post using `gh pr comment <PR_REF> --body "..."`.
  5. If **no** → tell the user: "Here's the command to use if you decide to post your comment from the CLI:" and show:
     ```
     gh pr comment <PR_REF> --body 'your comment text'
     ```
     Do not post. The user takes it from here.

### Review format

**If issues were found:**

```
# Code review: <repo> #<PR number>

Github: <https://github.com/OWNER/REPO/pull/PR_NUMBER>

---

Found N issues:

1. <brief description of bug> (CLAUDE.md says "<...>")

<link: https://github.com/OWNER/REPO/blob/FULL_SHA/path/to/file#L10-L14>
(Already raised: <link>)   ← omit this line if no existing comment matches

2. <brief description of bug> (bug due to <file and code snippet>)

<link: ...>
```

If `OUTPUT = github`, append:

```
🤖 Generated with [Claude Code](https://claude.ai/code)

<sub>- If this code review was useful, please react with 👍. Otherwise, react with 👎.</sub>
```

If `IS_AUTHOR = true` and `COMMIT_STYLE_NOTES` is non-empty, append after the main list (and after the footer if github):

```
## Commit message notes

<notes about commit message style>
```

**If no scored issues were found:**

```
### Code review

No issues found. Checked for bugs, CLAUDE.md compliance[, constitution compliance — omit if CONSTITUTION_PATH is null][, and PR-AGENT.md criteria — omit if PR_AGENT_PATH is null].
```

If `OUTPUT = github`, append:

```
🤖 Generated with [Claude Code](https://claude.ai/code)
```

---

## Step 9 — Finalize task list

**State check:** Step 8 is complete.

Call `TaskList`. For every task not in `completed` state (whether `pending` or `in_progress`), call `TaskUpdate` to mark it `completed`. This is a self-healing cleanup pass — it catches any step that was started but whose completion call was skipped during execution.

---

## Appendix A — Code linking format

Use this format precisely; the Markdown preview will not render other formats correctly:

```
https://github.com/OWNER/REPO/blob/FULL_SHA/path/to/file#L10-L15
```

Requirements:

- Full 40-character git SHA (not a branch name, tag, or `HEAD`)
- Repo name must match the repo under review
- `#` sign directly after the file name, no space
- Line range: `L[start]-L[end]`
- Provide at least 1 line of context before and after the line in question (e.g., if the issue is on line 6, link to `L5-L7`)
- Use `gh pr view` or `git rev-parse` to obtain the full SHA; do not construct it manually

**Empty-output fallback:** If a `grep` or `diff` command used to find line numbers returns no output, do not retry or pass the empty result onward — this will cause an API error. Instead, link to the file without a line range:

```
https://github.com/OWNER/REPO/blob/FULL_SHA/path/to/file
```

---

## Appendix B — False positive reference

Do not flag these as issues (for use in steps 4 and 5):

- Pre-existing issues not introduced by this PR
- Something that looks like a bug but is actually correct
- Pedantic nitpicks a senior engineer would not raise in review
- Issues a linter, typechecker, or compiler would catch — assume CI handles these; do not run builds
- General code quality concerns (test coverage, documentation, general security) unless explicitly required by CLAUDE.md or the constitution
- CLAUDE.md or constitution instructions explicitly silenced in the code (e.g., a lint-ignore comment)
- Changes in functionality that are likely intentional or directly related to the broader change
- If an unmodified line is a pre-existing early-return path or branch that was not updated to handle a concept or variable introduced by this PR, flag it — otherwise skip real issues on lines the PR author did not modify

---

## General notes

- Prefer GitHub MCP tools for all GitHub read operations — use `gh` CLI only when an MCP call explicitly fails or when there is no MCP equivalent (e.g., GraphQL edit history queries). Do not use web fetch.
- Make a todo list at the start (main session only — specialist and scoring sub-agents launched via the Agent tool do not create todo lists). Mark each step's task as completed immediately when that step finishes — do not batch task completion at the end.
- Cite and link every issue
- **Read files using the Read or Grep tools — do not use `cat`, Bash pipes, or inline Python to read tool result files or local code.** Bash tool calls require user approvals; Read and Grep do not. Use Read with `offset`/`limit` to access different sections of large files.
- **Do not write Bash commands consisting only of comments.** Express reasoning as text in your response — comment-only Bash calls require approval and produce no output.
- **Never use empty Bash output as message content.** If any command returns no output, treat it as "not found" and use the appropriate fallback (e.g., file-only link, skip that step). Passing an empty string as a content block causes a 400 API error.
- Do not run builds or type checks; CI handles these
- Keep the final comment brief; avoid emojis in the review body
