# Changelog

## 2026-09-08

- New step (5) recommends ticket-text edits for anything resolved this
  run — via the parent, the codebase, or the requester — so the same
  question doesn't have to be re-answered at the next grooming or
  estimate. Prefers rewording an existing sentence/bullet in place over
  bolting on a new one, and flags split recommendations separately
  since there's no sentence to reword for those.
- Fixed a real bug found in testing: after the requester answered grooming
  questions, the skill moved straight to estimating without checking whether
  they were actually done — a reply isn't the same as a go-ahead. Step 3 now
  explicitly asks "anything else, or should I go ahead?" after every round of
  answers and waits for a real confirmation before scoring, however many
  rounds that takes.
- The parent/epic ticket (when one exists via Linear/Jira/GitHub hierarchy) is
  now fetched at full depth and checked for answers *before* anything is
  flagged as an ambiguity, not just skimmed for dependency cross-referencing.
  Questions the parent already answers are cited (`PARENT_RESOLVED`) instead
  of being surfaced to you or the codebase check.
- Dependencies are now classified `sequencing` (shape is stable, just not landed
  yet — a scheduling fact) vs. `risk` (shape could still change — a complexity
  fact). Only `risk` dependencies push the Fibonacci estimate up; `sequencing`
  ones are still listed for planning but no longer stack into an inflated
  score. The 5/8 anchors and "why not lower/higher" guidance now say so
  explicitly, with a worked ✅/❌ example.
- Ask grooming questions before scoring, not after: flagged ambiguities are now
  surfaced to the requester between fetching and estimating, so answers can
  actually reduce the estimate's uncertainty instead of just being logged.
- New step checks the repo(s) the skill was launched from for answers to
  grooming questions before bothering the requester—single repo or a folder
  of sibling repos, both detected automatically. Code-derived answers are
  cited by file/line and never conflated with the requester's own answers.
- Drop the tiresome "for personal use only / nothing was written back"
  disclaimer.

## 2026-08-31

- README: prose and formatting cleanup

## 2026-08-14

- Initial release.
- Applied /improve-skill audit: verbatim read-only constraint on subagents, GitHub
  fetch fallback parity, all-tickets-failed STOP gate, scoring tie-breaker,
  ambiguity skip rule, output examples, trigger-first description, precondition
  annotations.
