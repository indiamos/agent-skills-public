---
name: review-plan
description: Use when reviewing a multi-task implementation plan — a Claude Code plan-mode plan or any saved markdown plan doc — before execution begins, or when the user asks to "review this plan," "check the plan for commit issues," or similar. Invoke with a path to the plan file.
argument-hint: "<path-to-plan-file>"
---

# Review Plan

## Context

A plan that issues a commit after every task can still get executed as one giant batch, because the commit mechanics were implied by the task structure rather than stated as a hard gate — leaving someone to unwind the working tree and reapply the diff by hand, task by task, after the fact. This skill audits a plan's text for the specific gaps that cause that failure mode and drafts exact rewrites before execution starts, so the policy is explicit instead of inferred.

Companion: `commit-plan` performs the after-the-fact reconstruction; this skill exists to make that reconstruction unnecessary.

## Step 0 — Bind target

**target**: path to the plan file, from the skill argument.

**STOP gate:** If no target was provided, ask: "Which plan file should I review?" Wait for a response before continuing.

Read the file at `target` and store its content as `PLAN_CONTENT`.

**STOP gate:** If the file cannot be read, report the error and halt.

**N/A gate:** If `PLAN_CONTENT` describes a single task, or a plan that produces no committed code changes (pure research, investigation, or a read-only audit), report "This plan has no commit boundaries to check — commit-mechanics review does not apply." and halt. Otherwise continue.

---

## Step 1 — Run the checklist

**Precondition:** `PLAN_CONTENT` is loaded and describes a multi-task plan that produces committed changes.

Check `PLAN_CONTENT` against every row below. Record each as `PASS`, `FAIL`, or `N/A`, with a one-line justification (quote the matching text for `PASS`, or state what's missing for `FAIL`).

✅ CORRECT:
`C1b — PASS: Global Constraints states "commit at the end of every task, before starting the next one — do not batch commits across tasks."`
`C4a — FAIL: no statement anywhere on whether commits are made during the run or left staged.`

❌ WRONG — no citation, no stated absence:
`C1b — PASS: looks fine.`
`C4a — FAIL: this is missing.`

| ID | Check |
|----|-------|
| C1a | Each task's commit step is phrased as a blocking gate ("do not begin Task N+1 until Task N's commit exists"), not a bare step titled "Commit" or a file listed only under a "Files" header |
| C1b | A Global Constraints section (or equivalent front-matter section) states the standing policy: commit at the end of every task, before the next task's steps begin — never batch commits across tasks |
| C1c | Every file touched by two or more tasks is flagged, at the point of overlap, with a note on commit ordering (e.g. "Task 4 touches this file again — commit Task 3's version first") |
| C1d | When a task modifies multiple files with different concerns (feature + test + lint), or when shared files are touched by multiple tasks, the plan classifies each file modification type: feature, test, lint, or tooling — enabling selective partial commits or targeted reverts if mid-task bugs surface |
| C2a | The commit convention — drafting skill/tool, ticket ID to tag, subject-line length limit, body wrap width — is stated once in Global Constraints, not re-specified or left ambiguous per task |
| C2b | If task commit steps issue literal `git commit` commands, the plan states that this must be checked against the executing agent's standing instructions (e.g. a rule to draft only and never run `git commit`) and resolved before Task 1 begins — not discovered after the last task |
| C3a | A fixup convention is stated once, for the case where implementing task N surfaces a bug in an already-committed earlier task: fixup-commit-and-squash-later, fix-forward, or amend — explicitly named, not left for the executing agent to improvise mid-plan |
| C3b | Each task's own tests are run immediately after being written and again after the implementation, before moving to the next task — not deferred into one verification pass at the end |
| C3c | When a task might surface a bug in an already-committed earlier task (C3a naming the fixup convention), the plan includes the exact git command sequence to apply and rebase the fixup commit (not just the convention name), e.g. "create a fixup commit with `git commit --fixup=<sha>`, then run `git rebase -i --autosquash` to integrate it" |
| C3d | If the fixup convention (C3a/C3c) relies on an interactive rebase (`git rebase -i --autosquash` or similar), the plan states that this must be checked against the executing agent's standing instructions/permissions before it's needed — interactive rebase is commonly denied outright by permission configs, the same class of conflict C2b flags for `git commit` |
| C4a | The plan states, once, in Global Constraints, whether it is to be executed with real commits made during the run or as staged diffs left for the user to commit |
| C4b | If subagents will execute individual tasks, that is stated up front, so tooling/permission expectations are set before execution rather than negotiated after |
| C4c | The plan states, once, whether per-task commits map one-to-one to pull requests or may be grouped into fewer, stacked PRs each containing multiple task commits — and if grouped, states explicitly that grouping does not require squashing those commits together |
| C4d | If the plan will produce multiple pull requests (e.g. a stacked PR series), Global Constraints states the total PR count and whether the executing agent should create them all in one pass or pause for confirmation between each — stated once, not discovered after the first PR is already created |
| C5 | A final self-check step requires confirming the commit boundary before declaring the plan done — e.g. `git log --oneline <base>..HEAD` and verifying exactly one commit per task, in task order |
| C6 | If the plan involves creating a branch, Global Constraints states that the executing agent must ask the user whether to use a worktree before creating one — default to no — rather than assuming a worktree (e.g. via an automatic branch-and-worktree step) |
| C7 | For tasks using check-then-act patterns (query state, then modify based on the result, especially with concurrent or multi-connection scenarios), the plan documents: what the race condition is, whether it requires atomic transaction wrapping, and if acceptable, why (e.g. "tokens expire in 90 days, connections are marked inactive in our system") |
| C8 | Before modifying tested code, the plan includes a step to run the existing test suite as a baseline — confirming tests pass before changes — then re-runs tests after implementation, rather than deferring verification to a single final pass |

**STOP gate:** If every check is `PASS` or `N/A`, report "No commit-mechanics gaps found." and halt — do not propose rewrites for a clean plan.

---

## Step 2 — Draft rewrites for each FAIL

**Precondition:** At least one check from Step 1 is `FAIL`.

For each `FAIL`, produce a concrete rewrite — not a description of what's missing. Group by target location:

- **Global Constraints edits** (C1b, C2a, C2b, C3a, C3d, C4a, C4b, C4c, C4d, C5, C6, C7): drafted as insertions into the plan's Global Constraints section. If that section does not exist, draft it as a new section to insert immediately after the plan's title/summary.
- **Per-task edits** (C1a, C1c, C1d, C3b, C3c): drafted per affected task, as the exact replacement text for that task's step list.

Use this format for every rewrite:

**Rewrite N** — `<Check ID>` · target: `<Global Constraints | Task N>`

**Replace:**

```
verbatim current text, or "(absent)" if the section/step doesn't exist yet
```

**With:**

```
drafted replacement text, ready to insert as-is
```

✅ CORRECT example:

**Rewrite 1** — `C1a` · target: `Task 3`

**Replace:**

```
### Task 3: Add run-status polling
- Implement `useRunStatus` hook
- Wire into `RunDetailView`
- Commit
```

**With:**

```
### Task 3: Add run-status polling
- Implement `useRunStatus` hook
- Wire into `RunDetailView`
- Run this task's tests; confirm they pass
- Commit per the convention in Global Constraints
- **Gate: do not begin Task 4 until this commit exists.**
```

❌ WRONG — vague, not a drafted replacement:

**Rewrite 1** — `C1a` · target: `Task 3`

**With:**

```
Make the commit step clearer and add a gate.
```

Do not draft rewrites for `PASS` or `N/A` checks.

---

## Step 3 — Present and confirm

Output, in full — do not summarize or abbreviate:

1. The complete Step 1 checklist table, every row, with its PASS/FAIL/N/A verdict and justification
2. Every Step 2 rewrite in full, with both `Replace` and `With` blocks

Then, as the final line of output, ask:

> Apply these changes to `<target>`? (yes / no / select)
> - **yes** — apply all rewrites
> - **no** — halt; leave the file unchanged
> - **select** — list each rewrite numbered; wait for the user to specify which to apply by number

Do not write to any file until the user responds. If running as a subagent, relay this output verbatim to the invoking agent or user before asking — do not summarize on their behalf.

---

## Step 4 — Apply changes

**Precondition:** The user has confirmed which rewrites to apply.

Apply each approved rewrite to `target` using targeted edits — replace only the text identified in `Replace`, leaving the rest of the plan unchanged. For rewrites where `Replace` is `(absent)`, insert the new section or step block at the location stated in Step 2.

If an edit fails because the `Replace` text no longer matches the file exactly (e.g. whitespace or formatting drifted since Step 2 drafted it), re-read the current file content at that location, adjust `Replace` to match verbatim, and retry once. If it still fails, skip that rewrite, note which one failed and why, and continue applying the rest.

After all edits are complete, report how many rewrites were applied, which checks they resolved, and any that failed.
