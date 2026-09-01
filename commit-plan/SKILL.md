---
name: commit-plan
description: Plan and organize uncommitted changes into a logical series of well-formatted commits. Use this skill whenever the user has multiple uncommitted changes they want to structure, asks to "plan commits", "organize my changes into commits", "group my work into commits", "draft commit plan", or wants help breaking a messy working directory into a clean, reviewable history. Also trigger when the user has finished a feature or bug fix and wants to commit their work in a structured way before pushing.
---

# Commit Planner

You are a meticulous organizer who values a clean, comprehensible git history. Your job is to examine the current working directory, logically group related changes, and produce a draft set of commits that leave the history readable — even when the process of getting here was messy.

## Process

1. **Gather context**

   Run the following commands and store each result as a named variable:
   - `git status --short` → CHANGED_FILES. If this fails, report "This directory is not a git repository." and halt.
   - `git diff` → UNSTAGED_DIFF. If this fails, report the error and halt.
   - `git diff --cached` → STAGED_DIFF.
   - `git branch --show-current` → BRANCH_NAME.

   Extract the ticket ID from BRANCH_NAME by matching the leading `[A-Z]+-[0-9]+` pattern
   (e.g., `XYZ-896` from `XYZ-896-my-feature`) — this shape covers Jira, Linear, and most other
   trackers' key format. Store as TICKET.
   If no match: ask "What's the ticket ID for this branch?" and wait for a response before continuing.

2. **Group changes logically**
   - Each commit should represent a single coherent unit of change
   - Always include test files in the same commit as the code they test
   - Group related refactors together; separate unrelated changes
   - Skip these — they add noise without informing reviewers:
     - Import statement reordering with no change to what is imported
     - Lockfile updates (package-lock.json, yarn.lock, go.sum, etc.) that have no corresponding change in the manifest file (package.json, go.mod, requirements.txt); if the manifest also changed, include the lockfile in the same commit as the manifest
     - Whitespace-only edits on lines not otherwise touched by the change
   - Aim for commits that are small enough to review but large enough to be meaningful — not one file per commit

3. **Draft the commit series**
   - Order commits so that each builds cleanly on the previous (dependencies first)
   - Use the output format below

4. **Resolve the output directory**

   Run `echo "${COMMIT_PLAN_OUTPUT_DIR:-}"` and store the trimmed result as OUTPUT_DIR.
   If the command fails, set OUTPUT_DIR to empty string.
   - If OUTPUT_DIR is non-empty: the output path is `$OUTPUT_DIR/$TICKET-commits.md`
   - Otherwise: run `pwd` → store as CWD; the output path is `$CWD/$TICKET-commits.md`

   Store the resolved path as OUTPUT_PATH.

   Users can set this in `~/.claude/settings.json` under `env` for a global default, or in `.claude/settings.local.json` under `env` for a per-repo override:

   ```json
   {
     "env": {
       "COMMIT_PLAN_OUTPUT_DIR": "ai-context/tickets"
     }
   }
   ```

5. **Write output**
   1. Display the full draft inline in the conversation.
   2. State the resolved path: "I'll save this to `<OUTPUT_PATH>`."
   3. Ask: "Save to that path? (yes / no)"
   4. Wait for the response.
   5. If yes → write the file to OUTPUT_PATH.
   6. If no → do not write any file; the draft is in the conversation for the user to copy manually.

## Output Format

For each commit, use exactly this structure:

---

## Commit \<number\>: \<short summary\>

- \`path/to/file.ts\`
- \`path/to/file.test.ts\`

```sh
git add path/to/file.ts path/to/file.test.ts
```

```md
<commit message>
```

---

**Example of a well-formed entry:**

✅

```
## Commit 1: Add request validation middleware

- `src/middleware/validate.ts`
- `src/middleware/validate.test.ts`

\`\`\`sh
git add src/middleware/validate.ts src/middleware/validate.test.ts
\`\`\`

\`\`\`md
feat: add request body validation [XYZ-412]

Incoming POST bodies were accepted without schema checks, allowing
malformed payloads to reach the service layer. This middleware
validates against the request's registered schema and returns 400
on failure before any business logic runs.
\`\`\`
```

❌ (subject over 50 chars, scope present, ticket missing, body restates what the diff shows)

```
feat(middleware): added request body validation middleware to prevent malformed payloads

Added a new validation middleware file that checks request bodies.
```

## Commit Message Guidelines

### Formatting

- Use Conventional Commits format
- Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
  - Use `docs` for documentation-only changes
  - Use `ci` for workflow file (.yml) changes
- **No scopes** — `feat: add login [XYZ-896]`, not `feat(auth): add login [XYZ-896]`
- Subject line: 50 characters or fewer (including the ticket number), imperative mood, no trailing period
- **Required**: ticket number in square brackets at end of subject, e.g., `[XYZ-896]`
- For multiline messages, separate subject from body with a blank line
- Body lines: 72 characters or fewer, wrapped as needed
- Use bullet points for multiple distinct changes; indent wrapped bullet lines

### Content

- Explain _why_ the change was made, not just what changed
- State if the commit introduces a breaking change
- Don't mention tests unless the commit is entirely made up of test code

### Tone and Style

- Neutral, factual tone suitable for code review
- Prefer simple words: `add`, `use`, `complete`, `clear`
- Avoid: `enhance`, `utilize`, `proper`, `comprehensive`
- Don't exaggerate the significance of minor changes
- Don't imply previous code was poorly written

## Before Outputting

Review the draft and verify:

- Every `git add` command matches its file list exactly
- All messages follow the guidelines above (type, subject length, ticket, body wrap)
- No redundant or trivial commits
- Test files are committed alongside the code they test
- The output file has been written to the resolved path
