---
name: cross-check-review
description: Cross-check a pr-scout review to decide which findings are worth flagging to the PR author. Use when reviewing someone else's PR — automatically adopts assessor perspective instead of implementor. Falls through to superpowers:receiving-code-review when the PR author is the authenticated GitHub user.
---

# Cross-Check PR Review

## Determine your role

Call `mcp__github__get_me` and extract `login`; store as `REVIEWER`.
If the call fails, fall back to:
    gh api user --jq '.login'
If both fail, report the error and halt; REVIEWER is required for routing.

Identify the PR author: check context first (pr-scout output, a recent `pull_request_read` result, or a PR URL mentioned in conversation). If not found, call `mcp__github__pull_request_read` with the PR reference and extract the author login. Store as `PR_AUTHOR`.

**STOP gate:** If PR_AUTHOR cannot be determined, report: "Cannot determine PR author — provide a PR number or URL, or run `/pr-scout` first." Halt.

- **`PR_AUTHOR == REVIEWER`** → invoke `superpowers:receiving-code-review` and follow it exactly
- **`PR_AUTHOR != REVIEWER`** → adopt Assessor mode below

## Verification (applies in all modes)

**Verify before flagging.** Before raising any concern, check whether the answer is already present in the files you have read. If you can answer your own question by reading the code, do so — confirm the concern is real or drop it.

If you are about to write "could", "might", "possible", "potentially", "it appears", "unclear whether", or "if [condition] holds" in a verdict, treat this as a signal that you have not finished verifying. Check the relevant code (call sites, guards, invariants) before assigning any verdict. Use conditional language only when the code is genuinely inaccessible — an external service, a closed-source library, or runtime-only behavior. An unverified hypothetical is worse than no finding.

## Assessor mode

You are evaluating a review of someone else's code. Your goal is to assess which findings are worth flagging to the author — not to fix anything yourself.

- Check each finding against codebase reality before forming an opinion
- Apply the YAGNI check for "professional features" (grep for actual usage)
- Treat reviewer claims as unverified hypotheses — check call sites, guards, and invariants before accepting them; a reviewer may lack full codebase context

If you cannot verify after checking: use **Unclear**, not **Flag**, and explain what you checked and what remains unresolved.

**Do not ask the user to make decisions.** Any open question about fix strategy, design trade-offs, or intent belongs to the PR author, not to the user. If a finding requires a judgment call, surface it as a question to raise with the author (in the Flag verdict), not as a question to the user.

For each finding, output one entry in this form:

✅ **Flag** — [one-sentence description of the confirmed issue, citing the specific code location]. Verified: [one sentence of evidence showing the concern is real and reachable].

✅ **Skip** — [one sentence explaining why the finding is incorrect, inapplicable, or YAGNI — e.g., no call sites found, concern already guarded, reviewer lacks context].

✅ **Unclear** — [one sentence describing what was checked and what the concern is]. Needs: [what additional information or access would be required to reach a verdict].

❌ **Flag** — "This could cause issues if X is empty." ← speculative; use Unclear, or check call sites and guards first.

Do not suggest implementing anything. Do not address the PR author directly.
