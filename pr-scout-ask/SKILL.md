---
name: pr-scout-ask
description: "Run after /pr-scout to convert a review file into question-framed comments — use when you want to send feedback as genuine questions rather than findings, so the PR author feels invited to explain rather than defend."
argument-hint: "[review-file.md]"
---

## Step 0 — Find the review file

**State check:** Read arguments.

- If arguments include a path to an existing review file, use it as `REVIEW_FILE`. Skip the search below.
- Otherwise, look for the most recently modified `pr-*-review.md` in the current working directory. Use the absolute path:

  ```sh
  ls -t $(pwd)/pr-*-review.md 2>/dev/null | head -1
  ```

  If a file is found and it is unambiguous (only one match, or one is clearly the most recent), proceed with it — do not ask for confirmation.

  If multiple files are found and it is unclear which to use, show the list and ask: "Which review file should I convert?" Wait for the response.

  If no file is found, report: "No review file found in the current directory. Run `/pr-scout` first to generate a review, or pass the file path as an argument." Halt.

Store the resolved path as `REVIEW_FILE`.

### 0b. Derive output path

Insert `-questions` before the `.md` extension:

- `pr-316-review.md` → `pr-316-review-questions.md`
- `path/to/review.md` → `path/to/review-questions.md`

Store as `QUESTIONS_FILE`.

If `QUESTIONS_FILE` already exists, ask: "[QUESTIONS_FILE] already exists. Overwrite? (yes / no)" Wait for response. If no, halt.

---

## Step 1 — Load the review

Read `REVIEW_FILE`. Extract each numbered issue: its description, code link, and any "Already raised" annotation.

**IMPORTANT: The review file may have been edited since it was written — for example, the reviewer may have deleted issues they decided not to raise. The file contents as read here are the sole authoritative source for which issues to convert. Do not supplement, restore, or carry forward any issue from earlier conversation context that is not explicitly present in the file.**

Store the list as `ISSUES`.

**State check:** If `ISSUES` is empty (e.g., the review says "No issues found"), report: "The review contains no issues to convert." Halt.

---

## Step 1.5 — Verify issues are still current

**State check:** `ISSUES` is bound and non-empty.

The PR author may have pushed new commits or rebased since the review was written. Before reframing, verify that each issue's referenced code still exists in the current PR diff.

1. Extract the PR owner, repo, and number from the code links in `ISSUES`.
2. Collect the unique set of file paths referenced across all issues.
3. For each unique file path, call `mcp__github__pull_request_read` with `method: "get_files"` and a small `perPage` value (e.g., 10), iterating through pages until all referenced paths are accounted for. Process only entries matching the paths in your set — skip unrelated files entirely.
4. For each issue:
   - If its file no longer appears in the PR diff at all, search the current PR diff for the specific code snippet or symbol the issue flagged. If a match is found in another file, update the issue's attachment point to the new location and carry it forward. If no match is found, flag it with `(original file no longer in diff; code not found elsewhere — issue may be resolved)` and carry it forward.
   - If the file is still in the diff but the specific line range no longer appears in the patch hunk, note that the line numbers may have shifted — carry the issue forward but flag it with `(line numbers may have shifted)` so the attachment header can be verified.

If any issues were flagged for manual verification, report the count briefly before continuing: e.g., "2 issues flagged for manual verification — file no longer in diff."

---

## Step 2 — Reframe each issue as a question

For each issue in `ISSUES`, rewrite it as a respectful, question-framed comment. Each question must:

- The author may have context you don't; frame questions so they can share it without feeling
  defensive. But don't undermine your own findings. If the review found that a specific code path has
  no deduplication, say so plainly and ask whether it's intentional, not whether you might be
  misreading it.
- Ask direct, answerable questions. Give the author something concrete to respond to — a yes/no
  choice, an either/or, or a specific thing to confirm. Avoid open-ended hedges like "could you help
  me understand the reasoning here?" which convince nobody that you respect their reasoning.

  Good: "Should we also run `make lint`, `make build`, and OpenAPI spec validation here? They're all
  listed as 'Pre-Merge Quality Gates' in `constitution.md`."
  Good: "Would it be out of scope to update that?"
  Bad: "Could you help me understand the reasoning here?"
  Bad: "I was wondering if there might be an issue with…"

- Include the key evidence from the original review inline: quote the specific code, name the
  relevant PRs or tickets, paraphrase what the code does. A question without evidence forces the
  author to go investigate before they can even understand what you're asking.
- Structure: lead with the question, then support it with evidence. For a short concern, the
  question can be the whole first sentence, with inline evidence after ("Do we want to also run
  `make lint` here? It's listed as a required gate in `constitution.md`."). For a complex concern,
  open with the question or a brief TL;DR, then elaborate with evidence. 1–6 sentences — don't
  pad, but don't dumb down. When a comment has a distinct question part and a distinct evidence
  part, separate them with a blank line — do not run them together into a single dense block.

  ✅ CORRECT:
  "Should we add a truncation indicator here? `internal/salesforce/client.go` line 76 reads up to
  32KB via `io.LimitReader(resp.Body, 32<<10)` and returns the body verbatim. If the response is
  exactly 32KB, the body has almost certainly been truncated — but the error message gives no
  indication of that, so an on-call engineer would have no way to know there's more context in
  Salesforce's logs."

  ✅ CORRECT (short form):
  "Do we want to also run `make lint`, `make build`, and OpenAPI spec validation here? They're all
  listed as Pre-Merge Quality Gates in `constitution.md`."

  ❌ WRONG (no evidence):
  "Should we indicate when the response body has been truncated?"

  ❌ WRONG (question buried at end):
  "`internal/salesforce/client.go` line 76 reads up to 32KB via `io.LimitReader` and returns the
  body verbatim. If the response is exactly 32KB it has almost certainly been truncated and the
  error message gives no indication of that. Should we add a truncation indicator?"

  ❌ WRONG (vague ask):
  "The response body may be truncated. Could you help me understand the intention here?"

- Preserve any "Already raised" annotation as-is.
- Determine the attachment type before writing each comment:
  - **Line-specific** — the concern applies to one contiguous passage, or the
    comment is short and generic enough to post identically at multiple spots
    (e.g., "Should we wrap this in `stack.Errorf()`?"): attach to one
    `[filename, lines X–Y]`. Record the first and last lines of the code selection
    alongside the line numbers — see Step 3 format.
  - **Cross-location** — the concern spans exactly two distinct passages and is
    substantive: choose the more relevant passage as the single attachment point;
    reference the other passage by name and line range in the comment body.
    Do not list two attachment headers for one comment.
  - **Whole-file** — the concern applies to the file as a whole, to lines outside
    the diff, or to more than two points in the same file: attach to `[filename]`
    with no line numbers.
  - **PR-level** — the concern applies to the entire PR, or spans more than two
    locations and the comment is longer than a few words: flag as a general PR
    comment; call out any specific file names and line ranges in the comment body.

**Tone target:** A PR author receiving these questions should feel invited to explain their
reasoning, not put on the defensive.

**Do not produce the following:**

- Rhetorical questions that imply a conclusion: "Wouldn't it make more sense to…?", "Isn't this the
  wrong approach for…?"
- Leading questions that embed an assertion: "Don't you think this will cause X?"
- Multi-part questions (more than one `?` per item) — split into separate items instead
- Statements reworded as questions by appending "right?" or "correct?": "This will always be nil
  here, right?"
- Questions that require no answer because the concern is self-evident from the diff alone
- An opening that names the attachment point: "In `filename.go` on lines 33–38…",
  "Looking at the code in `worker.go`…", or similar — the attachment header already
  establishes context. Name a file or line range in the body only when the referenced
  passage is different from the attachment point (cross-location or PR-level comments).

---

## Step 3 — Write the questions file

Compose the questions file and write it directly to `QUESTIONS_FILE` — do not print the content in chat first. If the user rejects the write, ask where they'd like to save it instead.

**Format:**

Group inline comments first (numbered), then any general PR comments. Use the
attachment type from Step 2.

```
# Review questions

## Inline comments

1. [filename, lines X–Y]
   First line of selection: `<verbatim first line of selected code>`
   Last line of selection:  `<verbatim last line of selected code>`

   _(Already raised: [link])_   ← include only if present in the original issue

   Question text.

   Second paragraph, if the concern has a distinct question part and evidence
   part that benefit from visual separation.

2. [filename]                                    ← whole-file: no line numbers

   Question text.

3. [filename-A, lines X–Y]                      ← cross-location: single anchor,
                                                    other location in body
   Question text referencing the other passage inline:
   "…the same issue also appears in [filename-B, L12–16](link)."

## General PR comments

- Question text. Any specific files or line ranges called out in the body.
```

To propose a specific code change inline, use GitHub's suggestion syntax (recognized
by GitHub's PR review editor and API):

````
```suggestion
replacement code here
```
````

Do not include a `🤖 Generated with Claude Code` footer.
