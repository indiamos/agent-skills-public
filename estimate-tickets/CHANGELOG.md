# Changelog

## 2026-10-16

- Added a company-rider hook: Step 4 and Step 6 now check for a sibling
  `SKILL.<company>.md` that defines a different client-facing point scale,
  and translate the final tier into it at output time while leaving the
  canonical 1/2/3/5/8 rubric, split tests, and examples untouched. Added
  the first such rider, for a client using a non-Fibonacci scale.

## 2026-09-08

- Reworked when Step 4 recommends splitting an 8, after finding in
  practice that splitting a two-risk ticket along risk-count alone (one
  risk per half) can produce two tickets each still gated on the exact
  same unresolved thing the original was — relabeled, not reduced. Now
  forks on *why* the ticket is an 8 before picking a test: risk-stacked
  8s go through an actionability test (a durability tier — untouched /
  call-site-only / not durable — plus a materiality floor, so a
  durable-but-1-point piece becomes a prep-work note instead of a second
  ticket); breadth-driven 8s (no risk dependency, just mechanical scope)
  go through a value-boundary test instead, since actionability is
  vacuous when nothing was blocked to begin with.
  Reviewability/parallelization/milestone reasons to split get their own
  process-note track that never changes the estimate. Fixed a related
  bug this surfaced: Step 5 would silently drop a split recommendation
  on a ticket where nothing else needed grooming. Research and rubric
  redraft by Perplexity; sources added to README > Acknowledgments.
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
