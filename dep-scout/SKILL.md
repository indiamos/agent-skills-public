---
name: dep-scout
description: "Use when reviewing a dependency-bump PR (dependabot, renovate, or human-authored security fix). Produces a traffic-light safety verdict with per-package changelog analysis, CI status, and security scan history. Invoke with a PR number or URL."
license: CC-BY-4.0
argument-hint: "PR-number-or-URL [file:output-path.md] [github]"
---

<!--
  Derived from pr-scout (dep-scout variant).
  Author: indiamos
  Purpose: dependency-bump PR review with traffic-light verdict.
  Ecosystems: Go modules, Ruby gems, npm/yarn.
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

  > ⚠️ GitHub MCP is [not installed / not enabled / not authenticated]. Without it, this skill issues multiple `gh` CLI calls — each of which may require an SSH fingerprint prompt on your machine.
  >
  > Proceed anyway? (yes / no)

  Wait for the user's response. If **no**, halt immediately. If **yes**, fall back to:

  ```sh
  gh api user --jq '.login'
  ```

  Store the result as `REVIEWER`. If this also fails, report the error and halt. Then continue to 0b.

### 0b. PR reference

Extract the PR reference from arguments (PR number, URL, or `owner/repo#number`). If no PR reference is present, ask the user: "Which PR should I review? Please provide a PR number, URL, or owner/repo#number." Wait for their response before continuing.

Store the normalized reference as `PR_REF`. Also extract `OWNER`, `REPO`, and `PR_NUMBER` from the reference (e.g., from `acme/widget-api#449`, extract `OWNER=acme`, `REPO=widget-api`, `PR_NUMBER=449`). When the user provides only a bare PR number, derive `OWNER` and `REPO` from the current git remote: run `git remote get-url origin` and parse accordingly.

### 0c. Timestamp

Run `date "+%Y-%m-%d-%H%M"` and store the result as `TIMESTAMP`. If the command fails or returns empty output, use only the date component from `currentDate` in context (formatted `YYYY-MM-DD`) and omit the time suffix — do not halt. This value must be set before the prompt below.

### 0d. Output path

Read the following files in order using the **Read tool only** (do not use `echo` or any Bash command — env vars are not reliably injected into skill context):

1. `~/.claude/settings.json` (user-level) — if its `env` object contains `DEP_SCOUT_OUTPUT_DIR`, store that value as `OUTPUT_DIR`. If `OUTPUT_DIR` is still empty and `PR_SCOUT_OUTPUT_DIR` is present, use that as the fallback `OUTPUT_DIR`. If it contains `DEP_SCOUT_DEFAULT_OUTPUT`, store as `DEFAULT_OUTPUT_MODE`.
2. `.claude/settings.json` relative to CWD (project-level) — same lookup; values override user-level.
3. `.claude/settings.local.json` relative to CWD (project-local, highest precedence) — same lookup; values override both.

Compute `DEFAULT_OUTPUT_PATH`:

- If `OUTPUT_DIR` is non-empty: `$OUTPUT_DIR/$TIMESTAMP-pr-$PR_NUMBER-dep-scout.md`
- Otherwise: no default path (must prompt)

Bind `OUTPUT` using the first matching rule below:

1. **Explicit arg — file**: If arguments include a token matching `file:<path>` or a path ending in `.md`, set `OUTPUT = file:<path>`. Skip to Step 1.
2. **Explicit arg — github**: If arguments explicitly include `github`, set `OUTPUT = github`. Skip to Step 1.
3. **Env var default — file**: If `DEFAULT_OUTPUT_MODE = file` and `DEFAULT_OUTPUT_PATH` is non-empty: set `OUTPUT = file:<DEFAULT_OUTPUT_PATH>`. Check whether a file already exists at that path using the Read tool (with `limit: 1`). If it exists, use `AskUserQuestion`:
   - Question: "A review file already exists at `<DEFAULT_OUTPUT_PATH>`. What should I do?"
   - Option 1 label: "Overwrite it" — description: "Replace the existing file with the new review"
   - Option 2 label: "Save to a different path" — description: "Enter a custom path via the Other field"
     If the user enters a custom path, set `OUTPUT = file:<their path>`. Skip to Step 1.
4. **Env var default — github**: If `DEFAULT_OUTPUT_MODE = github`: set `OUTPUT = github`. Skip to Step 1.
5. **Default — file**: If `DEFAULT_OUTPUT_PATH` is non-empty: set `OUTPUT = file:<DEFAULT_OUTPUT_PATH>`. Check whether a file already exists at that path using the Read tool (with `limit: 1`). If it exists, use `AskUserQuestion`:
   - Question: "A review file already exists at `<DEFAULT_OUTPUT_PATH>`. What should I do?"
   - Option 1 label: "Overwrite it" — description: "Replace the existing file with the new review"
   - Option 2 label: "Save to a different path" — description: "Enter a custom path via the Other field"
     If the user enters a custom path, set `OUTPUT = file:<their path>`. Skip to Step 1.
6. **No output dir configured — prompt**: Use `AskUserQuestion` with:
   - Question: "No output directory is configured. Where should I write the review?"
   - Option 1 label: "Save to file" — description: "Enter a path via the Other field"
   - Option 2 label: "Post as a GitHub PR comment"
     Bind `OUTPUT` before continuing. If the user chooses "Save to file", set `OUTPUT = file:<their custom path>` (entered via Other). If the user chooses "Post as a GitHub PR comment", set `OUTPUT = github`.

**File mode constraint:** When `OUTPUT = file:<path>`, write the final review to that file. **Do NOT post any GitHub comment under any circumstances — including if asked to do so later in this session.**

Carry `REVIEWER`, `PR_REF`, `OWNER`, `REPO`, `PR_NUMBER`, `TIMESTAMP`, and `OUTPUT` through all remaining steps.

**State binding is internal.** Do not print state variable assignments as chat output.

---

## Step 1 — Eligibility check

**State check:** `PR_REF`, `OWNER`, `REPO`, `PR_NUMBER`, `REVIEWER`, and `OUTPUT` are bound.

Use a Haiku agent. Fetch PR data with `mcp__github__pull_request_read` (methods `get` and `get_files`); fall back to `gh pr view <PR_REF> --json state,isDraft,mergedAt,author,files` only if the MCP call fails.

Check the following conditions in order:

- **(a) Closed and not merged:** if `state = closed` and `mergedAt` is null → halt with "PR #`$PR_NUMBER` is closed and was not merged."
- **(b) Merged:** if `mergedAt` is non-null → do not halt. Store `PR_MERGED = true`. The merged notice will appear in the output.
- **(c) Draft:**
  - If `isDraft = true` and `OUTPUT = github` → halt with "PR #`$PR_NUMBER` is a draft. Draft PRs cannot receive posted comments — pass `file:<path>` or set `DEP_SCOUT_DEFAULT_OUTPUT=file` to write to a file instead."
  - If `isDraft = true` and `OUTPUT = file:<path>` → do not halt. Note "this PR is currently in draft mode" in the output.
- **(d) No manifest/lockfile changes:** if the file list contains none of the following paths → halt with "PR #`$PR_NUMBER` contains no manifest or lockfile changes — nothing to review.":
  - `go.mod`, `go.sum`
  - `Gemfile`, `Gemfile.lock`
  - `package.json`, `yarn.lock`, `package-lock.json`
  - `Cargo.toml`, `Cargo.lock`
  - `requirements.txt`, `pyproject.toml`, `poetry.lock`, `Pipfile`, `Pipfile.lock`
- **(e) PR author:** always store `PR_AUTHOR = author.login`. This will appear in the PR header in the output.

**STOP gate:** Halt on conditions (a) or (d) as described. Halt on (c) only when `OUTPUT = github`. All other conditions continue.

---

## Step 2 — Parse PR

**State check:** Step 1 passed without halt.

Use a Haiku agent. Fetch PR data via `mcp__github__pull_request_read` with methods `get`, `get_diff`, and `get_commits`. Fall back to `gh` CLI only if MCP fails.

### PR title

From the `get` response, extract `title` and store as `PR_TITLE`.

### Linked issues

Parse the PR body text for:

- Standard GitHub close references: `Closes #N`, `Fixes #N`, `Resolves #N` (case-insensitive) → construct `https://github.com/$OWNER/$REPO/issues/N`
- Dependabot alert references: `Dependabot alert #N` or `security/dependabot/N` (case-insensitive) → construct `https://github.com/$OWNER/$REPO/security/dependabot/N`

Store extracted URLs as `LINKED_ISSUE_URLS` (may be empty).

### Package list

Parse the **diff** as the source of truth for version changes. Supplement with PR body notes for context. For each manifest file changed:

| File           | Parse rule                                                                                                |
| -------------- | --------------------------------------------------------------------------------------------------------- |
| `go.mod`       | `require` directive changes: lines of the form `module v_old` → `module v_new` (both direct and indirect) |
| `package.json` | `dependencies` and `devDependencies` version changes                                                      |
| `yarn.lock`    | Use only to confirm packages already found in `package.json`; do not use as sole source                   |
| `Gemfile`      | `gem 'name', 'v_old'` → `gem 'name', 'v_new'` changes                                                     |
| `Gemfile.lock` | Use only to confirm packages already found in `Gemfile`                                                   |

For each package found, build an entry:

```json
{
  "name": "string",
  "ecosystem": "go | npm | ruby",
  "old_version": "string",
  "new_version": "string",
  "pr_body_notes": "string",
  "linked_issue_urls": ["string"]
}
```

- `pr_body_notes`: for dependabot PRs, the per-package section of the PR body (the dependabot entry for this package); for human-authored PRs where the PR body is undifferentiated, include the entire PR body.
- `linked_issue_urls`: copy of `LINKED_ISSUE_URLS` for every package (agents need context on which security alert URL to fetch).

Store as `PACKAGES`.

**If `PACKAGES` is empty** after parsing (e.g., lockfile regeneration with no manifest version changes): skip Steps 3–4b. Proceed to Step 5 with `PACKAGE_RESULTS = []`.

---

## Step 3 — Per-package verification

**State check:** `PACKAGES` is non-empty. `OWNER` and `REPO` are bound.

> ⚡ **PARALLEL LAUNCH — send all per-package Task tool calls in a single message.**
>
> All per-package agents are independent. There are no dependencies between them. Do not launch any agent before the others; do not wait for one to finish before starting the next. Make all Task tool calls simultaneously in one response.
>
> If you intend to call multiple tools and there are no dependencies between the tool calls, make all of the independent tool calls in parallel. Maximize use of parallel tool calls to increase speed and efficiency.

Cap at 8 concurrent agents; if `PACKAGES` has more than 8 entries, queue the remainder and launch them as slots free.

Do not specify a model for these agents — use the operator default. This is the judgment-intensive step.

**No Bash tool in per-package agents — include this constraint verbatim in every agent prompt:**

> **CRITICAL — NO BASH TOOL.** Do not use the Bash tool for any purpose. Every Bash call requires a manual user-approval prompt and will block or abort the review. This means:
>
> - No `cat`, `grep`, `find`, `head`, `tail`, `sed`, or any shell command
>
> Read GitHub file contents with `mcp__github__get_file_contents`. Fetch GitHub releases with `mcp__github__list_releases`. Fetch registry pages with WebFetch. Search the repo with `mcp__github__search_code` or with the local `Grep` tool. Read local files with the `Read` tool.

Each agent receives the package entry from `PACKAGES` (all fields) and performs the following:

### 1. Context setup

Read `pr_body_notes` and `linked_issue_urls` from the package entry.

### 2. Dependabot alert (if present)

If a Dependabot alert URL is present in `linked_issue_urls`, fetch that page first as the primary source of truth for:

- CVE ID(s)
- CVSS score
- Affected version range
- Fixed-in version

Use this data to seed `security_fixes` before fetching the changelog.

### 3. Fetch changelog

Fetch the changelog between `old_version` and `new_version` using this fallback chain:

**Go modules:**

1. Parse `go.mod` (via the diff) for the module path (e.g., `golang.org/x/net`). Derive the GitHub org/repo from the module path (e.g., `github.com/golang/net`).
2. Try GitHub MCP releases: `mcp__github__list_releases` for the org/repo.
3. If releases are empty, try GitHub MCP file read: `mcp__github__get_file_contents` for `CHANGELOG.md` at the repo root.
4. If still nothing, note "no changelog source found" in `notes`.

**npm:**

1. Fetch the package registry entry at `https://registry.npmjs.org/<name>` via WebFetch to get the repository URL.
2. If the repository URL points to GitHub, try `mcp__github__list_releases`.
3. If releases are empty or the repo is not on GitHub, fetch `https://www.npmjs.com/package/<name>?activeTab=versions` via WebFetch.
4. If still nothing, note "no changelog source found".

**Ruby gems:**

1. Fetch `https://rubygems.org/gems/<name>` via WebFetch to get the source code repository URL.
2. If the URL points to GitHub, try `mcp__github__list_releases`.
3. If releases are empty or the repo is not on GitHub, fetch `https://rubygems.org/gems/<name>/versions` via WebFetch.
4. If still nothing, note "no changelog source found".

### 4. Scan changelog

Within the changelog entries that fall between `old_version` and `new_version` (inclusive of the new version, exclusive of the old), scan for:

- `BREAKING CHANGE` or `BREAKING` keywords
- Renamed, removed, or changed public APIs
- Deprecation notices
- Security advisories or CVE IDs

### 5. Breaking API usage check (major bumps only)

If `bump_type = "major"` and `breaking_changes` is non-empty: for each breaking API symbol, search the consuming repo's source using this fallback chain:

1. Any ask-mo code search tools available in the MCP servers
2. GitHub MCP code search: `mcp__github__search_code` with `repo:$OWNER/$REPO <symbol>`
3. Local file search: use the `Grep` tool with pattern `<symbol>` on the repository root — do not use Bash.

If **zero results** are returned from all sources, treat the breaking API as not used by this repo. Add "no usage of `<symbol>` found in repo" to `notes`.

If results are found, list the file paths in `notes` so the reviewer can inspect them.

### 6. Return result

```json
{
  "name": "string",
  "bump_type": "patch | minor | major",
  "breaking_changes": ["string"],
  "security_fixes": ["CVE-YYYY-NNNNN — short description (source URL)"],
  "changelog_url": "string | null",
  "notes": "string"
}
```

- `bump_type`: determined by comparing `old_version` and `new_version` according to semver rules (major component changed → major; only minor component changed → minor; only patch changed → patch).
- `security_fixes`: one entry per CVE or advisory; format: `CVE-YYYY-NNNNN — short description (source URL)`. Include the Dependabot alert URL or NVD URL as source.
- `changelog_url`: the URL of the most useful changelog source found (GitHub releases page URL, or direct CHANGELOG.md URL). `null` if no source was found.

Store combined results as `PACKAGE_RESULTS`.

**STOP gate:** If all agents fail, report the errors and halt. If some agents fail, proceed with successful results and note which packages could not be verified — treat them as 🟡 in Step 5.

After all agents return, call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 4 — CI status

**State check:** Steps 1–3 completed (or `PACKAGES` was empty and Step 3 was skipped).

Use a Haiku agent. Fetch check-run results for the PR head commit via `mcp__github__pull_request_read` with method `get_check_runs`. Fall back to `gh pr checks <PR_REF> --json name,state,conclusion` if MCP fails.

Classify status:

- All checks passing or skipped → `CI_STATUS = passing`
- Any check failing → `CI_STATUS = failing`; record names of failing checks as `CI_FAILING_CHECKS`
- Any check pending, none failing → `CI_STATUS = pending` (treat as passing — branch protections prevent merging if CI later fails)
- No checks found → `CI_STATUS = no_checks`

Store `CI_STATUS` and `CI_FAILING_CHECKS`.

After completing this step, call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 4b — Security scan check

**State check:** Steps 1–4 completed.

Use a Haiku agent.

### 1. Fetch all PR comments

Call `mcp__github__pull_request_read` with method `get_comments`. Fall back to:

```sh
gh api repos/$OWNER/$REPO/issues/$PR_NUMBER/comments
```

### 2. Detect scanner comments

Find comments from bot accounts whose body contains a security scanner summary table. A comment qualifies if its body contains **at least 3** of these strings (case-sensitive):

- `Vulnerabilities`
- `Sensitive Data`
- `Secrets`
- `IaC Misconfigurations`
- `SAST Findings`
- `Software Management Findings`
- `Total`

### 3. Fetch comment edit history

For each qualifying comment, fetch its edit history using `gh` CLI. No GitHub MCP tool covers GraphQL comment edit history — this `gh` call is intentional and mandatory (not a fallback):

```sh
# Step a: get comment node IDs for the scanner bot
gh api repos/$OWNER/$REPO/issues/$PR_NUMBER/comments \
  --jq '.[] | select(.user.login == "<scanner_login>") | {id: .node_id, login: .user.login}'
```

```sh
# Step b: fetch edit history for each node ID
gh api graphql -f query='{
  node(id: "NODE_ID") {
    ... on IssueComment {
      userContentEdits(last: 10) { nodes { editedAt diff } }
    }
  }
}'
```

### 4. Parse findings

For each qualifying comment, produce one entry:

- `scanner`: the bot login (e.g., `wiz-e9eb886e02-04-21-26[bot]`)
- `current_findings`: parse the **most recent** version of the comment body. For each category row in the summary table, extract the count (treat `"-"` as 0). Set `total` to the sum across all categories.
- `originally_flagged`: `true` if the edit history `diff` shows that any prior version of the comment had a non-zero total. Look for lines like `+| Vulnerabilities | 7 |` or `+| Total | 7 |` in the diff (the `+` prefix indicates a line that was present before and was later changed or removed). If `originally_flagged = true` and `current_findings.total = 0`, the scanner found issues that were subsequently resolved.

If multiple comments exist from the same scanner bot, use the **most recent by `created_at`** for `current_findings`; check edit history on **all** of them for `originally_flagged`.

Store as `SCAN_RESULTS` (array). If no qualifying scanner comments are found, store `SCAN_RESULTS = []`.

After completing this step, call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 5 — Verdict synthesis

**State check:** `PACKAGE_RESULTS`, `CI_STATUS`, and `SCAN_RESULTS` are available.

### Per-package verdict

Assign a verdict to each entry in `PACKAGE_RESULTS` using the first matching row:

| Condition                                     | Verdict                         |
| --------------------------------------------- | ------------------------------- |
| New version itself carries an unresolved CVE  | 🔴                              |
| Major bump, breaking APIs used by repo        | 🔴                              |
| Major bump, changelog unreadable or not found | 🔴                              |
| Patch bump, breaking changes present          | 🟡                              |
| Minor bump with deprecations                  | 🟡                              |
| Agent failed to verify this package           | 🟡                              |
| Major bump, breaking APIs not used by repo    | 🟢 (add note: "no usage found") |
| Minor bump, no breaking changes               | 🟢                              |
| Patch bump, no breaking changes               | 🟢                              |

### Overall verdict

Apply the following rules in order (first match wins):

1. Any package is 🔴 → Overall 🔴
2. `CI_STATUS = failing` → Overall 🔴
3. Any entry in `SCAN_RESULTS` has `current_findings.total > 0` → Overall 🔴
4. Any package is 🟡 → Overall 🟡
5. All packages 🟢, CI passing or pending or no_checks, all scanners clean or `SCAN_RESULTS = []` → Overall 🟢
6. `PACKAGE_RESULTS = []` (lockfile regeneration only) → Overall 🟢

Entries in `SCAN_RESULTS` where `originally_flagged = true` but `current_findings.total = 0` are **informational only — no color penalty**.

### Recommendation text

- 🟢 (packages present): "Safe to merge."
- 🟢 (regeneration, `PACKAGE_RESULTS` empty): "Lockfile regeneration only — no package version changes detected."
- 🟡: "Review before merging — `<specific items from PACKAGE_RESULTS and/or CI>`."
- 🔴: "Do not merge — `<specific reason>`."

Store as `VERDICT` (overall color emoji) and `RECOMMENDATION` (full text).

After completing synthesis, call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 5b — Late eligibility re-check

**State check:** `VERDICT` and `RECOMMENDATION` are set.

Use a Haiku agent to verify the PR is still open and check whether it has been converted to draft since Step 1.

**STOP gate:** If the PR is now closed, halt with "PR #`$PR_NUMBER` closed after review started — output suppressed." If it has been converted to draft and `OUTPUT = github`, halt with "PR #`$PR_NUMBER` converted to draft — cannot post comment; pass `file:<path>` or set `DEP_SCOUT_DEFAULT_OUTPUT=file` to write to a file instead." If it has been converted to draft and `OUTPUT = file:<path>`, notify the user ("Note: this PR was converted to draft after the review was completed") and continue to Step 6.

After the agent returns, call `TaskUpdate` to mark this step's task `completed` before proceeding.

---

## Step 6 — Write output

**State check:** `VERDICT` and `RECOMMENDATION` are set. Eligibility confirmed.

### Compose the review

Build the review text using the template below. Omit rows and sections as specified by the row rules.

```markdown
# dep-scout: PR #$PR_NUMBER — $VERDICT $RECOMMENDATION_SHORT

|            |                                                              |
| ---------- | ------------------------------------------------------------ |
| **PR**     | [$PR_TITLE](https://github.com/$OWNER/$REPO/pull/$PR_NUMBER) |
| **Author** | @$PR_AUTHOR                                                  |

_Note: this PR has already been merged._
↑ Include only if `PR_MERGED = true`.

## Recommendation

$RECOMMENDATION

## $name $old_version → $new_version ($bump_type) — $pkg_verdict

|                      |                                       |
| -------------------- | ------------------------------------- |
| **Breaking changes** | $breaking_changes_text                |
| **Security fixes**   | $security_fixes_text                  |
| **Changelog**        | [$name release notes]($changelog_url) |
| **References**       | [#N](url), [#M](url)                  |

_(repeat ### block for each package)_

---

- $CI_LINE
- $SCANNER_LINE
```

**Row rules:**

- `Breaking changes`: always shown. If none: "None".
- `Security fixes`: always shown. If none: "None".
- `Changelog`: omit the row if `changelog_url` is null.
- `References`: show linked GitHub issues (`/issues/N` URLs) only — Dependabot alert URLs (`/security/dependabot/N`) are already hyperlinked in `Security fixes`. Omit the row if no `/issues/N` URLs are present.

**CI line variants:**

- `CI_STATUS = passing`: `- **CI:** ✅ All checks passing`
- `CI_STATUS = failing`: `- **CI:** ❌ Failing: check1, check2` (list `CI_FAILING_CHECKS`)
- `CI_STATUS = pending`: `- **CI:** ⏳ Pending (treated as passing)`
- `CI_STATUS = no_checks`: `- **CI:** ℹ️ No checks configured`

**Security scanner line variants (one per scanner in `SCAN_RESULTS`; if `SCAN_RESULTS` is empty, show the "none" line):**

- Clean, never flagged: `- **$scanner:** ✅ Clean`
- Clean, originally flagged: `- **$scanner:** ✅ Clean — originally flagged N findings (resolved prior to merge)`
- Currently flagged: `- **$scanner:** ❌ N findings`
- No scanner found: `- **Security scanner:** ℹ️ No scanner findings reported`

**CVE formatting in Security fixes cells:** hyperlink CVE IDs to the Dependabot alert URL when available (already in `linked_issue_urls`); otherwise link to `https://nvd.nist.gov/vuln/detail/$CVE_ID`. Format: `[CVE-YYYY-NNNNN](url) — short description`.

**`RECOMMENDATION_SHORT`**: the first sentence of `RECOMMENDATION`, without the specific item list. E.g., "Safe to merge." or "Review before merging." or "Do not merge."

**Multi-package PRs:** one `###` block per package (all packages), then the shared CI/scanner list, then one overall `### Recommendation`.

### Write output

**If `OUTPUT = file:<path>`:**
Write the review text to `<path>`. Confirm in chat: "Review written to `<path>`."

**If `OUTPUT = github`:**
Display the full comment text in chat first. Ask: "Post this as a comment on PR #$PR_NUMBER? (yes / no)"

- If yes: run `gh pr comment <PR_REF> --body "<review_text>"` to post.
- If no: display the `gh pr comment` command so the user can run it manually.

After writing or posting the review, call `TaskUpdate` to mark this step's task `completed` before proceeding to Step 7.

---

## Step 7 — Finalize task list

**State check:** Step 6 is complete.

Call `TaskList`. For every task not in `completed` state (whether `pending` or `in_progress`), call `TaskUpdate` to mark it `completed`. This is a self-healing cleanup pass — it catches any step that was started but whose completion call was skipped during execution.

---

## General notes

- **MCP-first, gh fallback.** Use GitHub MCP tools for all GitHub read operations. Fall back to `gh` CLI only when no MCP tool covers the operation (e.g., GraphQL comment edit history in Step 4b), or when an MCP call explicitly fails.
- **No Bash for state.** Never use `echo` or Bash to read env vars — they are not reliably injected into skill context. Always use the Read tool to check settings files.
- **Parallel agents.** All per-package agents in Step 3 are independent. Launch all simultaneously in one response (subject to the 8-agent cap).
- **No silent failures.** If a step fails and the skill continues, note the failure in the output (which packages could not be verified, which check-run data could not be fetched, etc.).
- **Task tracking.** Call `TaskCreate` for each step at the start of the skill. Mark each task `in_progress` before starting and `completed` when done. Do not batch completions at the end of the skill.
- **State binding is internal.** Never print state variable assignments as chat output.
