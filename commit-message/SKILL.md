---
name: commit-message
description: Generate a clear, conventional commit message from a git diff. Use when writing a commit message, reviewing staged changes, or fixing an existing message that doesn't follow the rules.
---

# Commit Message Skill

Generate consistent, informative commit messages inspired by the Conventional Commits specification.

## When to Use This Skill

- User asks to "commit", "draft a commit message", "write a commit message", or "prepare commit"
- User wants to fix or rewrite a commit message you already proposed
- Before any `git commit` command

## Process

1. **Survey the working tree.** Do NOT assume changes are staged — VSCode commits all working changes by default, so the unstaged diff is often what the user wants to commit.

   `<use_parallel_tool_calls>` Run the following three commands in a single parallel tool-call batch:

   | Command              | Purpose                                        |
   | -------------------- | ---------------------------------------------- |
   | `git status --short` | Which files are staged, unstaged, or untracked |
   | `git diff --staged`  | Staged diff                                    |
   | `git diff`           | Unstaged diff                                  |

   If any command fails (e.g., not in a git repo, or git is unavailable), report the error and halt. If `git status --short` shows nothing staged but the working tree has changes, treat the unstaged + untracked changes as the intended commit scope.

2. **Identify the type** from the table below.
3. **Draft the message** following the format and rules below.
4. **Verify the subject line length** BEFORE presenting it. Run `printf '%s' '<candidate subject>' | wc -c`. Store the number. If it is 51 or more, rewrite and re-run — do not present any subject line whose verified count is > 50. Mental counting is unreliable; this command is the source of truth.
5. **Present the message** in a fenced block so the user can copy it into their editor. Do NOT run `git commit` — the user commits themselves.

## Commit Message Format

```
<type>: <description> [TEAM-123]

[optional body]

[optional footer(s)]
```

Do NOT use scopes (e.g., `feat(auth):`). This project does not use them.

### Types

| Type       | Description                                          |
| ---------- | ---------------------------------------------------- |
| `feat`     | New feature or user-visible capability               |
| `fix`      | Bug fix                                              |
| `docs`     | Documentation only                                   |
| `refactor` | Code change that neither fixes a bug nor adds a feat |
| `perf`     | Performance improvement                              |
| `test`     | Adding or fixing tests                               |
| `build`    | Build system or dependency changes                   |
| `ci`       | CI configuration                                     |
| `chore`    | Maintenance tasks that don't fit elsewhere           |
| `revert`   | Revert a previous commit                             |

### Subject Line Rules

- **Max 50 characters, counting the ENTIRE line.** This includes the type, colon, space, description, space, and ticket reference in brackets — every character, including punctuation and whitespace. Do not count only the description.
- **Verify the count with a shell command, not mental counting.** For each candidate subject line, run:

      printf '%s' 'YOUR SUBJECT LINE HERE' | wc -c

  Store the result. If it is 51 or more, rewrite the subject and re-run the command. Only present subject lines you have verified this way — mental counting has been unreliable in practice, which is why this step exists.

- Example: `printf '%s' 'fix: prevent duplicate items on click [XYZ-234]' | wc -c` → `48` ✅
- Example: `printf '%s' 'fix: prevent duplicate cart items on reclick [XYZ-234]' | wc -c` → `54` ❌ Too long, rewrite.
- Use imperative mood: "add" not "added" or "adds".
- Don't capitalize the first letter after the colon.
- No period at the end.

### Ticket References

- When the work is associated with a tracked ticket (Jira, Linear, Shortcut, etc.), include the reference in square brackets at the end of the subject line (e.g., `[XYZ-123]`, `[ENG-456]`).
- The ticket reference counts toward the 50-character limit.

### Body (when needed)

- Separate from subject with a blank line.
- Explain _why_ the change was made, not just what changed.
- Wrap at 72 characters.
- Use bullet points for multiple changes.
- **Wrap code-like tokens in backticks.** This includes variable names, function names, type names, file paths, env var names, CLI flags, config keys, and commands. The user edits commit messages in their editor, not the command line, so backticks are safe.
  - Yes: ``Add debounce to `handleAddToCart` and check `cartItems` before insertion.``
  - No: `Add debounce to handleAddToCart and check cartItems before insertion.`

### Footer (when needed)

- `BREAKING CHANGE:` for breaking changes
- `Fixes #123` to close issues
- `Refs #456` to reference without closing
- For commits responding to a PR review comment, end the body with:
  ```
  Per @<author>'s comment
  <URL to the specific review comment>
  ```

## Examples

### Simple feature

```
feat: add fuzzy matching to search [XYZ-789]

Implement Levenshtein distance for typo tolerance in search queries.
Configurable via the `FUZZY_THRESHOLD` env var.
```

### Bug fix

```
fix: prevent duplicate cart items [XYZ-234]

Add debounce to `handleAddToCart` and check `cartItems` for an existing
entry before insertion.

Fixes #234
```

### Breaking change

```
feat!: switch response to JSON:API [XYZ-567]

BREAKING CHANGE: API responses now follow the JSON:API spec. All
clients need to update their parsers.

- Wrap payload in a `data` object
- Move metadata to a `meta` object
- Add `links` for pagination
```

### Refactor with multiple changes

```
refactor: consolidate auth logic [XYZ-890]

- Extract JWT handling into `AuthTokenService`
- Move session management from the controller to middleware
- Add refresh token rotation in `refreshSession`

Prepares for the upcoming OAuth2 integration.
```

## Output

When generating a commit message:

1.  Briefly summarize the changes (1–2 lines).
2.  Present the proposed commit message in a fenced code block.
3.  Show the verified subject-line length as the literal command output, so the user can audit it:

        $ printf '%s' 'fix: prevent duplicate items [XYZ-234]' | wc -c
        41

    If you skipped running `wc -c` for any reason, say so explicitly — do not claim a count you did not verify.

4.  If the type is non-obvious, explain the choice in one sentence.
5.  Ask whether to proceed or revise.
