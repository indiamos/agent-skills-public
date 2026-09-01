# Instruction Pattern Catalog

Sources: `~/repos/advisor/.claude/commands/` (all .md files), `~/.claude/skills/pr-scout/SKILL.md`, `~/.claude/skills/export-full/SKILL.md`, `~/.claude/skills/pr-scout-ask/SKILL.md`

---

## Pattern: Argument binding

**What it's for:** Read a value from user-provided arguments (or a prior prompt response); pause to ask if the value is absent.
**Outcome type(s):** PRODUCES, PAUSES

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 0b
[TRIGGER] Step 0 begins
[OUTCOME] PRODUCES PR_REF, or PAUSES to ask user if no PR reference present
[PATTERN] Argument binding
[TEXT] Extract the PR reference from arguments (PR number, URL, or
       owner/repo#number). If no PR reference is present, ask the user:
       "Which PR should I review? Please provide a PR number, URL, or
       owner/repo#number." Wait for their response before continuing.
       Store the normalized reference as PR_REF.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 0b | Bind PR_REF from arguments; pause if absent |
| SKILL.md (pr-scout) | Step 0e | Check for `commits` token in args; set CHECK_COMMITS (no prompt) |
| SKILL.md (export-full) | Arguments section | SESSION_REF/OUTPUT_PATH from 0/1/2 args; ambiguous single arg → pause to ask |
| SKILL.md (pr-scout-ask) | Step 0 | REVIEW_FILE from arg if provided; else auto-discover via `ls -t` |
| speckit.analyze.md | Step 0 / User Input | Consider $ARGUMENTS before proceeding if not empty |
| speckit.checklist.md | Step 0 / User Input | Consider $ARGUMENTS before proceeding if not empty |
| speckit.clarify.md | Step 0 / User Input | Consider $ARGUMENTS before proceeding if not empty |
| speckit.constitution.md | Step 0 / User Input | Consider $ARGUMENTS before proceeding if not empty |
| speckit.implement.md | Step 0 / User Input | Consider $ARGUMENTS before proceeding if not empty |
| speckit.plan.md | Step 0 / User Input | Consider $ARGUMENTS before proceeding if not empty |
| speckit.specify.md | Step 0 / User Input | Feature description is the argument; error if empty |
| speckit.tasks.md | Step 0 / User Input | Consider $ARGUMENTS before proceeding if not empty |
| speckit.taskstoissues.md | Step 0 / User Input | Consider $ARGUMENTS before proceeding if not empty |

---

## Pattern: Command binding

**What it's for:** Run a tool call (shell command, API call, or script) and store the result as a named variable; halt or abort if the call fails.
**Outcome type(s):** PRODUCES, HALTS

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 0a
[TRIGGER] Step 0 begins
[OUTCOME] PRODUCES REVIEWER, or HALTS if the gh api call fails
[PATTERN] Command binding
[TEXT] Run: gh api user --jq '.login'
       Store the result as REVIEWER. If this fails, report the error and halt.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 0a | Bind REVIEWER via `gh api user` (fallback when MCP unavailable) |
| SKILL.md (pr-scout) | Step 0c | Bind PR_AUTHOR via `mcp__github__pull_request_read`; derive IS_AUTHOR |
| SKILL.md (pr-scout) | Step 3 | `pull_request_read` → extract headRefOid as COMMIT_SHA |
| SKILL.md (pr-scout) | Step 7.5 | Fetch existing PR comments via `mcp__github__pull_request_read`; fall back to `gh pr view` |
| SKILL.md (export-full) | find-current | Run `export-session.py find-current`; parse JSONL, SESSION_START, OUTPUT_DIR in one call |
| SKILL.md (export-full) | Timestamp extraction | Run `export-session.py timestamp <jsonl>`; STOP gate if exits non-zero |
| SKILL.md (export-full) | Conversion | Run `jsonl-to-transcript.py`; STOP gate if non-zero or no output file produced |
| SKILL.md (export-full) | After conversion | Run `export-session.py finalize`; STOP gate if exits non-zero |
| SKILL.md (pr-scout-ask) | Step 0 | Run `ls -t $(pwd)/pr-*-review.md` to find most recent review file; STOP gate if none found |
| SKILL.md (pr-scout-ask) | Step 1.5 | `mcp__github__pull_request_read` with `get_files` for each referenced file path |
| speckit.specify.md | Step 2a–c | Run `git fetch --all --prune`, then `git ls-remote` + `git branch` to find highest feature number |
| speckit.specify.md | Step 2d | Run `create-new-feature.sh --json` to produce BRANCH_NAME and SPEC_FILE |
| speckit.clarify.md | Step 1 | Run `check-prerequisites.sh --json --paths-only`; abort if JSON parsing fails |
| speckit.analyze.md | Step 1 | Run `check-prerequisites.sh --json --require-tasks --include-tasks`; abort if any required file is missing |
| speckit.plan.md | Step 1 | Run `setup-plan.sh --json`; parse FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH |
| speckit.tasks.md | Step 1 | Run `check-prerequisites.sh --json`; parse FEATURE_DIR and AVAILABLE_DOCS |
| speckit.implement.md | Step 1 | Run `check-prerequisites.sh --json --require-tasks --include-tasks` |
| speckit.implement.md | Step 4 | Run `git rev-parse --git-dir` to detect if repo is git-managed |
| speckit.implement.md | Step 4 | Run `.specify/scripts/bash/update-agent-context.sh claude` (via plan.md phase 1) |
| speckit.taskstoissues.md | Step 3 | Run `git config --get remote.origin.url` to get GitHub remote |
| speckit.constitution.md | Step 4 | Read all dependent template files to propagate consistency |

---

## Pattern: Precondition annotation

**What it's for:** Document what state must be true at the start of a step — a structural convention declaring assumed state, not an enforced check.
**Outcome type(s):** (meta — no runtime outcome)

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 1
[TRIGGER] Step 1 begins
[OUTCOME] (meta) documents that PR_REF and REVIEWER must be bound
[PATTERN] Precondition annotation
[TEXT] State check: PR_REF is bound; REVIEWER is bound.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 1 | "State check: PR_REF is bound; REVIEWER is bound." |
| SKILL.md (pr-scout) | Step 2 | "State check: Step 1 passed without halt." |
| SKILL.md (pr-scout) | Step 3 | "State check: CLAUDE_MD_PATHS is available." |
| SKILL.md (pr-scout) | Step 4 | "State check: PR_SUMMARY and COMMIT_SHA are available." |
| SKILL.md (pr-scout) | Step 5 | "State check: ALL_ISSUES is collected (may be empty)." |
| SKILL.md (pr-scout) | Step 6 | "State check: SCORED_ISSUES is available (may be empty)." |
| SKILL.md (pr-scout) | Step 7 | "State check: HIGH_CONFIDENCE_ISSUES and any COMMIT_STYLE_NOTES are ready." |
| SKILL.md (pr-scout) | Step 7.5 | "State check: HIGH_CONFIDENCE_ISSUES is ready. If empty, skip this step." |
| SKILL.md (pr-scout) | Step 8 | "State check: OUTPUT is bound from step 0. Eligibility confirmed." |
| SKILL.md (pr-scout) | Step 4.5 | "State check: ALL_ISSUES is collected. If empty, skip to step 5." |
| SKILL.md (pr-scout-ask) | Step 0 | "State check: Read arguments." |
| SKILL.md (pr-scout-ask) | Step 1.5 | "State check: ISSUES is bound and non-empty." |
| speckit.plan.md | Phase 1 | "Prerequisites: research.md complete" |
| speckit.tasks.md | Step 2 note | "Note: Not all projects have all documents. Generate tasks based on what's available." |

---

## Pattern: STOP gate

**What it's for:** A binary guard — if a condition is true, halt with an explanatory message; otherwise proceed normally with no special action.
**Outcome type(s):** HALTS

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 1
[TRIGGER] Eligibility agent returns results
[OUTCOME] HALTS if (a) PR is closed or (c) PR does not need review; proceeds normally otherwise
[PATTERN] STOP gate
[TEXT] STOP gate: If (a) or (c) is true, report which condition matched
       and halt. If (b) is true and OUTPUT = github, report that the PR
       is a draft and halt. Do not proceed to step 2.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 1 | Halt if PR is closed or trivially OK; draft+github also halts |
| SKILL.md (pr-scout) | Step 2 | Halt if repo access error |
| SKILL.md (pr-scout) | Step 4 | Halt if all six agents returned errors |
| SKILL.md (pr-scout) | Step 7 | Halt if PR is now closed; halt if converted to draft + github output |
| SKILL.md (export-full) | Arguments section | Labeled "STOP gate" but PAUSES — ask user if SESSION_REF cannot be determined |
| SKILL.md (export-full) | Safety Checks | JSONL file not found → list three most recent files and halt |
| SKILL.md (export-full) | Safety Checks | JSONL file is empty → halt |
| SKILL.md (export-full) | Timestamp extraction | Script exits non-zero → halt; do not substitute today's date |
| SKILL.md (export-full) | After conversion | `finalize` exits non-zero → halt; do not proceed with a potentially corrupted file |
| SKILL.md (pr-scout-ask) | Step 0 | No review file found → report and halt |
| SKILL.md (pr-scout-ask) | Step 1 | ISSUES is empty → report "no issues to convert" and halt |
| speckit.implement.md | Step 2 | Halt (after user confirmation) if checklists are incomplete and user says no |
| speckit.taskstoissues.md | Step 3 | Halt (CAUTION block) if remote is not a GitHub URL |
| speckit.clarify.md | Step 1 | Abort if JSON parsing fails |
| speckit.analyze.md | Step 1 | Abort with error if any required file is missing |
| speckit.specify.md | Step 4 | ERROR if no feature description provided; ERROR if no user scenarios determinable |

---

## Pattern: Conditional routing

**What it's for:** Route execution to two or more meaningfully different paths based on a value; halt may be one branch among others.
**Outcome type(s):** BRANCHES

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 0d
[TRIGGER] Inspecting OUTPUT mode argument
[OUTCOME] BRANCHES: sets OUTPUT = file:<path>, OUTPUT = github, or PAUSES to ask user
[PATTERN] Conditional routing
[TEXT] Inspect arguments:
       - If arguments include a token matching file:<path> or a path ending
         in .md, set OUTPUT = file:<path>. Skip the prompt below.
       - If arguments explicitly include "github", set OUTPUT = github.
         Skip the prompt below.
       - Otherwise: ask the user where to write the review (file or GitHub).
         Wait for the response. Set OUTPUT accordingly.
       File mode constraint: when OUTPUT = file:<path>, do NOT post any
       GitHub comment under any circumstances.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 0★ | MCP call success/auth-error/not-found → different handling; failure route prompts user to proceed anyway |
| SKILL.md (pr-scout) | Step 0d | 5-rule priority cascade for OUTPUT: file arg → github arg → env-file → env-github → prompt |
| SKILL.md (pr-scout) | Step 1 | After eligibility agent returns: different actions for (a)/(b)/(c)/(d) conditions |
| SKILL.md (pr-scout) | Step 6b | Commit style handling branches on IS_AUTHOR and CHECK_COMMITS values |
| SKILL.md (pr-scout) | Step 6c | Empty-result handling: IS_AUTHOR + COMMIT_STYLE_NOTES branches |
| SKILL.md (pr-scout) | Step 7 | Re-check: closed → halt; converted to draft + github → halt; converted to draft + file → notify and continue |
| SKILL.md (pr-scout) | Step 8 | Route review to file or GitHub with different sub-flows |
| SKILL.md (export-full) | Arguments section | One arg: route on .jsonl/UUID vs .md/.txt/path vs ambiguous → ask |
| SKILL.md (export-full) | Choosing output directory | OUTPUT_PATH bound → skip section; else use OUTPUT_DIR or CWD fallback |
| SKILL.md (pr-scout-ask) | Step 0 | Zero/one/multiple review files found → halt / proceed / ask which |
| SKILL.md (pr-scout-ask) | Step 1.5 | Issue file in diff / not in diff / line range shifted → update / flag / carry forward |
| SKILL.md (pr-scout-ask) | Step 2 | 4-way attachment type: line-specific / cross-location / whole-file / PR-level |
| speckit.implement.md | Step 2 | If checklists directory exists, scan for incomplete items; branch on PASS/FAIL |
| speckit.implement.md | Step 2 | If checklists fail: ask user whether to proceed; branch on yes/no response |
| speckit.specify.md | Step 6c | If [NEEDS CLARIFICATION] markers remain: branch on marker count and resolution state |
| speckit.specify.md | Step 6c | If items fail: re-run validation iterations; branch if still failing after 3 rounds |
| speckit.clarify.md | Step 4 | Sequential questioning loop: branch on user answer type, disambiguation needed, early termination signals |
| speckit.constitution.md | Step 2 | CONSTITUTION_VERSION bump type: branch on major/minor/patch rules |

---

## Pattern: Parallel dispatch

**What it's for:** Launch multiple agents simultaneously to perform independent work; collect all results before proceeding.
**Outcome type(s):** DISPATCHES

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 4
[TRIGGER] PR_SUMMARY is available
[OUTCOME] DISPATCHES 6 parallel agents, each reviewing the PR from a different perspective; collects combined issue list
[PATTERN] Parallel dispatch
[TEXT] <use_parallel_tool_calls>
       Launch 6 parallel specialist agents simultaneously:

       | Agent | Scope |
       |-------|-------|
       | CLAUDE.md audit | CLAUDE.md compliance only |
       | Bug scan | Logic errors, null deref, off-by-one |
       | Git history | Regressions vs prior commits |
       | Previous comments | Issues raised in earlier reviews |
       | Code comments | Comment accuracy and completeness |
       | Code-path/struct invariants | Struct field consistency |

       Each agent must:
       - Return a list of issues with a fully-formed link
         (https://github.com/OWNER/REPO/blob/FULL_SHA/path#L10-L14)
         captured at identification time — do NOT return partial
         references (line numbers only) requiring a follow-up fetch.
       - NOT re-run shell commands already executed in prior steps.
       After all agents return: if all failed, halt; if some failed,
       proceed with results from successful agents and note failures.
       Store the combined issue list as ALL_ISSUES.
```

**Common misapplications:**

- **Ordered list format**: Writing agents as `a.`, `b.`, `c.` causes the LLM to execute them sequentially. Use a table or add `<use_parallel_tool_calls>` explicitly.
- **Agent scope creep**: Agents that re-run shell commands from prior steps introduce inconsistency and waste tokens. Scope each agent to its specific task; route unverifiable cases through the scoring rubric's lower confidence tiers instead of re-fetching.
- **Partial artifacts**: Agents that return line numbers without full file paths force a follow-up fetch. Require agents to produce fully-formed artifacts (complete URLs, fully-qualified references) at identification time.
- **Dispatching when sequential is correct**: Parallel dispatch is wrong when sub-tasks share state, build on each other's output, or require context from a prior sub-task's result. Use sequential steps for those; reserve dispatch for genuinely independent work.
- **Missing constraint rationale**: Agent constraints written as bare prohibitions ("do not run shell commands") are less reliable than constraints with a brief reason ("do not run shell commands — unverifiable cases belong in the rubric's 25-point tier"). One clause is enough; the goal is intelligibility, not justification.
- **Missing model specification**: Naming a model in prose is not the same as specifying it in the invocation.

  ❌ "launch a parallel Haiku agent for each issue"
  ✅ "launch a parallel agent with `model: \"haiku\"` for each issue"

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 4 | 6 parallel Sonnet specialist agents for review |
| SKILL.md (pr-scout) | Step 5 | Parallel Haiku scoring agents launched for every issue in ALL_ISSUES (one per issue); agents are prohibited from running shell commands — unverifiable cases use the 25-point rubric tier |
| SKILL.md (pr-scout) | Step 4.5 | Verification agents for hypothetical-language issues; all launched in a single parallel batch with model: "sonnet" |
| speckit.plan.md | Phase 0, Step 2 | Research agents dispatched for each unknown in Technical Context |

---

## Pattern: Scoring rubric

**What it's for:** A labeled scale with explicit, per-level criteria that a scoring agent uses to assign a numeric confidence or quality score.
**Outcome type(s):** PRODUCES

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 5
[TRIGGER] Each scoring agent receives an issue to evaluate
[OUTCOME] PRODUCES a confidence score 0–100 for that issue
[PATTERN] Scoring rubric
[TEXT] Each scoring agent returns a confidence score 0–100. Rubric:
       - 0: Not confident at all. False positive or pre-existing issue.
       - 25: Somewhat confident. Might be real, may also be false positive.
             Unable to verify. If stylistic, not in the relevant CLAUDE.md.
       - 50: Moderately confident. Verified as real but might be a nitpick
             or rare in practice. Not very important relative to the PR.
       - 75: Highly confident. Double-checked, very likely real, will be hit
             in practice. Very important, or directly mentioned in CLAUDE.md.
       - 100: Absolutely certain. Confirmed real, will happen frequently.
              Evidence directly confirms it.
       For CLAUDE.md-flagged issues: must double-check CLAUDE.md actually
       calls out the specific issue before scoring above 50.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 5 | 0–100 confidence scale with five labeled levels |
| speckit.analyze.md | Step 5 | CRITICAL/HIGH/MEDIUM/LOW severity heuristic for findings |
| speckit.checklist.md | Step 5 | Quality dimension tags [Completeness/Clarity/etc.] as categorized rubric |

---

## Pattern: Output format spec

**What it's for:** Define the exact structure, required fields, ordering, and ✅/❌ examples for a document or message the skill must produce.
**Outcome type(s):** PRODUCES

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 8, "Review format"
[TRIGGER] Composing the final review document
[OUTCOME] PRODUCES the review document in a specified format
[PATTERN] Output format spec
[TEXT] If issues were found:
         ### Code review
         Found N issues:
         1. <brief description> (CLAUDE.md says "<...>")
            <link: https://github.com/OWNER/REPO/blob/FULL_SHA/path#L10-L14>
            _(Already raised: <link>)_   ← omit if no existing comment matches
       If no scored issues:
         ### Code review
         No issues found. Checked for bugs and CLAUDE.md compliance.
       If OUTPUT = github, append footer with 🤖 attribution line.
       If IS_AUTHOR = true and COMMIT_STYLE_NOTES non-empty, append
         ## Commit message notes
         <notes>
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 8 "Review format" | Final review document with issues-found and no-issues variants |
| SKILL.md (pr-scout) | Appendix A | Code linking format spec: exact URL structure, 40-char SHA, line range |
| SKILL.md (pr-scout-ask) | Step 3 | Review questions file: `## Inline comments` / `## General PR comments` sections; numbered items with attachment-type header, first/last code selection lines, question body |
| speckit.analyze.md | Step 6 | Analysis report format: findings table with ID/Category/Severity/Location/Summary/Recommendation |
| speckit.analyze.md | Step 6 | Coverage summary table, constitution issues section, unmapped tasks section, metrics block |
| speckit.checklist.md | Step 6 | Checklist file format: H1 title, purpose/created meta, `##` category sections, `- [ ] CHK### item` lines |
| speckit.checklist.md | Step 2 | Question table format: Option / Candidate / Why It Matters columns |
| speckit.specify.md | Step 6c | Clarification question format: `## Question [N]`, Context, What we need to know, Suggested Answers table |
| speckit.tasks.md | Step 4 | Task checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path` |
| speckit.implement.md | Step 2 | Checklist status table: Checklist / Total / Completed / Incomplete / Status columns |
| speckit.constitution.md | Step 5 | Sync Impact Report as HTML comment: version change, modified/added/removed sections, templates requiring updates |

---

## Pattern: Preview-then-confirm

**What it's for:** Show the composed output to the user and wait for explicit approval before writing to a file, posting, or taking an irreversible action.
**Outcome type(s):** PAUSES

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 8, OUTPUT = github sub-flow
[TRIGGER] OUTPUT = github and review document is composed
[OUTCOME] PAUSES: prints full review in chat; waits for yes/no before posting
[PATTERN] Preview-then-confirm
[TEXT] OUTPUT = github → preview flow:
       1. Print the full composed review in the chat.
       2. Ask: "Post this comment to the PR? (yes / no)"
       3. Wait for the response.
       4. If yes → post using gh pr comment <PR_REF> --body "..."
       5. If no → show the CLI command and do not post.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 8, github output sub-flow | Full preview + yes/no confirmation before posting PR comment |
| SKILL.md (export-full) | Safety Checks, output file | If output path exists: show size and first line, ask "Overwrite? (y/n)" before proceeding |
| speckit.implement.md | Step 2 | Display incomplete checklist table; ask "proceed anyway?"; wait before continuing |
| speckit.analyze.md | Step 8 | Ask user whether to suggest remediation edits; do NOT apply automatically |
| speckit.specify.md | Step 6c | Present all clarification questions together; wait for user responses before updating spec |
| speckit.clarify.md | Step 4 | Present one question at a time; wait for accepted answer before advancing |

---

## Pattern: Skip rule

**What it's for:** Explicit criteria for what to exclude from processing — categories, conditions, or items that must not be flagged, generated, or acted upon.
**Outcome type(s):** (meta — no runtime outcome)

**Authoring note:** Prefer positive framing over negative ("produce X" rather than "do not produce Y") when possible. When a negative constraint is necessary, append a brief reason in the same line — bare prohibitions are less reliably followed than prohibitions with a stated reason. One clause is enough: "do not do Z — because Y."

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Appendix B
[TRIGGER] Agents evaluating potential issues
[OUTCOME] (meta) lists what must not be flagged
[PATTERN] Skip rule
[TEXT] Do not flag these as issues:
       - Pre-existing issues not introduced by this PR
       - Something that looks like a bug but is actually correct
       - Pedantic nitpicks a senior engineer would not raise
       - Issues a linter/typechecker/compiler would catch
       - General code quality concerns unless required by CLAUDE.md
       - CLAUDE.md instructions silenced in the code
       - Changes in functionality likely intentional or related to the change
       - Real issues on lines the PR author did not modify — EXCEPTION:
         a pre-existing early-return not updated to handle a concept
         introduced by this PR is fair game
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Appendix B | Eight categories of issues that must not be flagged |
| SKILL.md (pr-scout) | Step 6b (CHECK_COMMITS = false) | Remove commit style issues; do not surface in any form |
| SKILL.md (pr-scout) | Step 6b (IS_AUTHOR = false) | Remove commit style issues entirely when reviewer is not the author |
| SKILL.md (pr-scout) | Step 5 non-empty guard | Skip any issue with a blank or whitespace-only description before launching scoring agent |
| SKILL.md (export-full) | Two separate calls | Don't prefix commands with variable assignments; don't chain with &&/;/backslash — breaks allowlist match |
| SKILL.md (pr-scout-ask) | Step 1 | "Do not supplement, restore, or carry forward any issue from earlier conversation context not explicitly in the file" |
| SKILL.md (pr-scout-ask) | Step 2 "Do not produce the following" | Prohibited question patterns: rhetorical, leading, multi-part, statement-as-question, self-evident, opening with attachment point |
| SKILL.md (pr-scout-ask) | Step 3 | Do not include a 🤖 footer |
| speckit.checklist.md | Step 5 "ABSOLUTELY PROHIBITED" | Items starting with Verify/Test/Confirm/Check + implementation behavior are forbidden |
| speckit.tasks.md | Task Generation Rules | Tests are OPTIONAL; only generate if explicitly requested |
| speckit.clarify.md | Step 3 | Exclude questions already answered, trivial stylistic preferences, plan-level execution details |
| speckit.analyze.md | Step 4 | Limit to 50 findings; aggregate remainder in overflow summary |
| speckit.specify.md | General Guidelines | DO NOT include implementation details (languages, frameworks, APIs, code structure) in the spec |

---

## Pattern: Annotation tagging

**What it's for:** Label items in a list with a status marker before presenting them.
**Outcome type(s):** PRODUCES

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 7.5
[TRIGGER] Checking HIGH_CONFIDENCE_ISSUES against existing PR comments
[OUTCOME] PRODUCES annotated issue list with "Already raised" markers
[PATTERN] Annotation tagging
[TEXT] For each issue in HIGH_CONFIDENCE_ISSUES, check whether any existing
       comment substantively raises the same concern (semantic match, not
       literal). If a match is found, append a note to that issue's output:
         _(Already raised: [link to comment])_
       Obtain the comment URL from the API response (html_url field).
       Do not @mention or name the comment author.
       Store the annotated list back as HIGH_CONFIDENCE_ISSUES.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 7.5 | Append "Already raised: [link]" to issues matching existing comments |
| SKILL.md (pr-scout-ask) | Step 1.5 | Flag stale issues with "(original file no longer in diff; code not found elsewhere — issue may be resolved)" or "(line numbers may have shifted)" |
| SKILL.md (pr-scout-ask) | Step 2 | Preserve "Already raised" annotation from source review when reframing each issue as a question |
| speckit.checklist.md | Step 5 | Tag each item with [Completeness], [Clarity], [Gap], [Ambiguity], etc. |
| speckit.analyze.md | Step 5 | Tag each finding with CRITICAL/HIGH/MEDIUM/LOW and category prefix (A1, B2, etc.) |
| speckit.tasks.md | Step 4 | Tag tasks with [P] (parallelizable) and [US1]/[US2]/etc. (user story) markers |
| speckit.specify.md | Step 4 | Mark unclear spec aspects with `[NEEDS CLARIFICATION: specific question]` |

---

## Pattern: File-conditional

**What it's for:** Execute a step only if a specific file, directory, or artifact exists; skip or branch otherwise.
**Outcome type(s):** BRANCHES

### Canonical example

```txt
[FILE] speckit.implement.md
[LOCATION] Step 2
[TRIGGER] Step 2 begins
[OUTCOME] BRANCHES: if FEATURE_DIR/checklists/ exists, scan and evaluate;
          otherwise skip checklist gating entirely
[PATTERN] File-conditional
[TEXT] Check checklists status (if FEATURE_DIR/checklists/ exists):
       - Scan all checklist files in the checklists/ directory
       - Count total, completed, and incomplete items
       - Display a status table and calculate overall PASS/FAIL
       - If any checklist is incomplete: stop and ask user
       - If all complete: automatically proceed to step 3
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 0d | Read PR_SCOUT_OUTPUT_DIR from three settings files in cascade; later files override earlier |
| SKILL.md (pr-scout-ask) | Step 0b | If QUESTIONS_FILE already exists → ask "Overwrite? (yes / no)"; halt if no |
| speckit.implement.md | Step 2 | Execute checklist gate only if checklists/ directory exists |
| speckit.implement.md | Step 3 | Read data-model.md, contracts/, research.md only if they exist |
| speckit.implement.md | Step 4 | Create .dockerignore only if Dockerfile*exists; .eslintignore if .eslintrc* exists; etc. |
| speckit.tasks.md | Step 2 | Load data-model.md, contracts/, research.md as optional (if they exist) |
| speckit.plan.md | Phase 1 | Conditionally update agent-specific context file based on which AI agent is in use |
| speckit.constitution.md | Step 1 | "If `.specify/memory/constitution.md` does not exist yet, copy the template first." |

---

## Pattern: Verbatim constraint injection

**What it's for:** A constraint that must be copied word-for-word into every subagent prompt to ensure uniform enforcement — used when a paraphrased instruction is insufficient for consistent behavior across parallel agents, or when the agent may deprioritize guidance that is not stated explicitly.
**Outcome type(s):** DISPATCHES (shapes agent prompt content)

**Authoring note:** Mark the constraint block clearly (bold header + block quote or distinct callout) and say "include this constraint verbatim in every agent prompt" — that phrasing signals to the orchestrator that copy-paste, not paraphrase, is required. Keep the constraint block self-contained: it will be read without surrounding context by the receiving agent.

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 4
[TRIGGER] Composing each specialist agent prompt
[OUTCOME] DISPATCHES agents whose prompts contain the exact verbatim constraint block
[PATTERN] Verbatim constraint injection
[TEXT] **No Bash tool in specialist agents — include this constraint verbatim
       in every agent prompt:**
       > CRITICAL — NO BASH TOOL. Do not use the Bash tool for any purpose.
       > Every Bash call requires a manual user-approval prompt and will block
       > or abort the review. This means:
       > - No cat, grep, find, head, tail, sed, or any shell command
       > - No gh pr diff, gh pr view, gh pr show, git log, git blame
       > - No inline Python or shell pipelines
       > Read GitHub file contents with mcp__github__get_file_contents.
       > Read the PR diff with mcp__github__get_pull_request_files.
       > Read local files with the Read tool; search local files with the Grep tool.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 4 | "No Bash tool" — must appear verbatim in every specialist agent prompt |
| SKILL.md (pr-scout) | Step 4 | "Verify before flagging" — must appear verbatim in every specialist agent prompt |
| SKILL.md (pr-scout) | Step 4.5 | "No Bash tool" — same constraint applied to verification agents |

---

## Pattern: Self-healing cleanup pass

**What it's for:** A terminal step that calls TaskList and marks any task not already in `completed` state as `completed` — a defensive finalization that ensures the skill ends cleanly even if a prior step's task-completion call was skipped due to an error or early branch.
**Outcome type(s):** PRODUCES

**Authoring note:** Place this as the last numbered step, after all output has been written. It is not a substitute for per-step completion calls — it catches the remainder. Describe it explicitly as "self-healing cleanup" so the executing agent treats it as idempotent bookkeeping, not a sign of a problem.

### Canonical example

```txt
[FILE] SKILL.md (pr-scout)
[LOCATION] Step 9
[TRIGGER] Step 8 is complete
[OUTCOME] PRODUCES fully-completed task list; no tasks left in pending/in-progress state
[PATTERN] Self-healing cleanup pass
[TEXT] Call TaskList. For every task not in completed state (whether pending or
       in_progress), call TaskUpdate to mark it completed. This is a self-healing
       cleanup pass — it catches any step that was started but whose completion
       call was skipped during execution.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout) | Step 9 | Scans all tasks after output is written; marks any uncompleted task as completed |

---

## Pattern: Currency verification

**What it's for:** Before acting on references to external data (code locations, file paths, line numbers), check whether those references are still valid in the current system state. Annotate stale references rather than silently acting on them or silently dropping them.
**Outcome type(s):** BRANCHES, PRODUCES

**Authoring note:** Trigger this whenever the skill reuses artifacts collected in a prior session or prior step — review files, cached line numbers, stored code links. Include both a "code moved" path (find the new location) and a "code gone" path (flag as possibly resolved). Report a count of flagged issues before continuing so the user can decide whether to intervene.

### Canonical example

```txt
[FILE] SKILL.md (pr-scout-ask)
[LOCATION] Step 1.5
[TRIGGER] ISSUES is loaded and non-empty; PR may have received new commits since review was written
[OUTCOME] BRANCHES: updates attachment point if code moved; annotates with staleness flag
          if unresolvable; proceeds unchanged if references are still current
[PATTERN] Currency verification
[TEXT] For each issue:
       - If its file no longer appears in the PR diff, search the current diff
         for the specific code snippet or symbol the issue flagged. If a match
         is found in another file, update the attachment point and carry forward.
         If no match is found, flag with "(original file no longer in diff;
         code not found elsewhere — issue may be resolved)" and carry forward.
       - If the file is still in the diff but the specific line range no longer
         appears in the patch hunk, flag with "(line numbers may have shifted)".
       If any issues were flagged, report the count briefly before continuing.
```

### All instances

| File | Location | Notes |
| ------ | ---------- | ------- |
| SKILL.md (pr-scout-ask) | Step 1.5 | Verify each issue's referenced file/lines are still in the current PR diff before reframing |

---

## Summary

| Pattern | Instance count | Files it appears in |
|---|---|---|
| Command binding | 21 | pr-scout, speckit.specify, speckit.clarify, speckit.analyze, speckit.plan, speckit.tasks, speckit.implement, speckit.taskstoissues, speckit.constitution, export-full, pr-scout-ask |
| Conditional routing | 18 | pr-scout, speckit.implement, speckit.specify, speckit.clarify, speckit.constitution, export-full, pr-scout-ask |
| Argument binding | 13 | pr-scout, speckit.analyze, speckit.checklist, speckit.clarify, speckit.constitution, speckit.implement, speckit.plan, speckit.specify, speckit.tasks, speckit.taskstoissues, export-full, pr-scout-ask |
| Skip rule | 13 | pr-scout, speckit.checklist, speckit.tasks, speckit.clarify, speckit.analyze, speckit.specify, export-full, pr-scout-ask |
| Precondition annotation | 14 | pr-scout, speckit.plan, speckit.tasks, pr-scout-ask |
| STOP gate | 16 | pr-scout, speckit.implement, speckit.taskstoissues, speckit.clarify, speckit.analyze, speckit.specify, export-full, pr-scout-ask |
| Output format spec | 11 | pr-scout, speckit.analyze, speckit.checklist, speckit.specify, speckit.tasks, speckit.implement, speckit.constitution, pr-scout-ask |
| File-conditional | 8 | speckit.implement, speckit.tasks, speckit.plan, speckit.constitution, pr-scout, pr-scout-ask |
| Annotation tagging | 7 | pr-scout, speckit.checklist, speckit.analyze, speckit.tasks, speckit.specify, pr-scout-ask |
| Preview-then-confirm | 6 | pr-scout, speckit.implement, speckit.analyze, speckit.specify, speckit.clarify, export-full |
| Scoring rubric | 3 | pr-scout, speckit.analyze, speckit.checklist |
| Parallel dispatch | 4 | pr-scout, speckit.plan |
| Verbatim constraint injection | 3 | pr-scout |
| Self-healing cleanup pass | 1 | pr-scout |
| Currency verification | 1 | pr-scout-ask |
