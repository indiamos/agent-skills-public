# estimate-tickets

Estimate one or more tickets on a Fibonacci complexity scale, flagging what needs refinement and what depends on other work the ticket doesn't explicitly note.

## Context

Story points are usually estimated by gut feel during a meeting. This skill supports (BUT IS NOT MEANT AS A SUBSTITUTE FOR) human estimation, using the ticket text: it fetches the ticket and, at full depth, its parent/epic (plus sibling titles/status for dependency context), estimates it against a Fibonacci scale with explicit anchors, and writes out *why*—including why it the estimate isn't one notch higher or lower. It also surfaces two things that often get missed until mid-sprint: acceptance criteria vague enough to need a refinement conversation, and dependencies on other tickets that aren't declared as a formal blocker.

Works across Linear, Jira, GitHub Issues, and Shortcut. Which tracker a bare ticket ID belongs to is configurable per repo (see Configuration)—or just pass a full ticket URL, and it will be inferred automatically.

**This skill is read-only against the tracker.** It never posts a comment, sets an estimate/story-point field, or changes status. Output is a Markdown file for your own reference.

## Usage

```txt
/estimate-tickets ACME-173
/estimate-tickets ACME-173 ACME-175 ACME-176
/estimate-tickets https://linear.app/acme/issue/ACME-173/some-title
/estimate-tickets ACME-173 file:~/estimates/acme-173.md
```

Pass one or more ticket references as bare IDs or full URLs. Mixed trackers are fine to use within the same run. If a ticket has ambiguous scope, the skill checks three places for an answer, in order, before bothering you: the ticket's parent/epic (if it's linked via the tracker's native hierarchy—Linear parent/child, Jira epic link, GitHub sub-issues), then the repo(s) you launched it from—existing patterns, config values, sibling endpoints, the repo layout itself—then finally you, for whatever's still open. Answer what you already know and anything still open goes into the doc as a grooming item. Produces one Markdown file with a section per ticket: the estimate and reasoning, a refinement checklist noting what was answered by the parent ticket, what was answered from code, what you answered, and what's still open, a dependency list split into what the ticket states explicitly versus what looks like a dependency but isn't declared as one, and—for anything that got resolved this run—suggested ticket-text edits so the next person estimating or grooming it doesn't have to re-derive the same answer.

## Configuration

| Env var | Purpose | Default |
| --- | --- | --- |
| `BASE_TICKET_URL` | Base URL used to resolve bare ticket IDs for this repo—e.g., `https://linear.app/acme/issue/` or `https://my-jira.atlassian.net/browse/`. Shared with `generate-pr-description`: set it once, and both skills will use it. | none; asks once per run if a bare ID needs it |
| `TICKET_LABEL` | Display label for the tracker (`Jira`, `Linear`, `Shortcut`, `GitHub`). If unset, inferred from `BASE_TICKET_URL`'s hostname. | inferred |
| `ESTIMATE_TICKETS_OUTPUT_DIR` | Directory where the output Markdown file is written. | current working directory |

Set in your Claude settings (`~/.claude/settings.json`, or per-repo in
`.claude/settings.json` / `.claude/settings.local.json`):

```json
{
  "env": {
    "BASE_TICKET_URL": "https://linear.app/acme/issue/",
    "TICKET_LABEL": "Linear",
    "ESTIMATE_TICKETS_OUTPUT_DIR": "~/working-docs/estimates"
  }
}
```

Output filenames include a timestamp and the ticket ID(s)—e.g., `2026-08-14-1127-estimate-acme-173.md`.

## The Fibonacci scale

| Value | Anchor |
| --- | --- |
| 1 | Purely mechanical, no judgment—e.g., duplicate-and-rename, add a link, copy change. |
| 2 | Mechanical but touches more than one place, or needs a small judgment call. |
| 3 | Mechanical plus a first-time-tooling learning curve or a lint/test/config verification loop. No open design decisions. |
| 5 | Real investigation or design ambiguity, a correctness/security-sensitive area, or one genuine *risk* dependency (its shape could still change)—but potentially still one bounded PR. |
| 8 | Multiple unresolved external decisions, infra blast radius, or several independent *risk* dependencies stacked together; flag for splitting into smaller slices—but only when a split actually unlocks something, see below. |

Every estimate includes why that number was chosen and not the ones adjacent to it.

**Dependencies count only if they're a genuine risk, not just a wait.** A dependency whose shape is already fully defined and just hasn't merged yet is *sequencing*—it's a scheduling fact, not a complexity fact, and doesn't raise the score no matter how many of them stack up. A dependency whose contract, spec, or decision is still unsettled is *risk*, and that's what actually earns a 5 or 8. Both kinds are still listed in the Dependencies section for planning purposes; sequencing ones are just called out as not affecting the number.

**A split recommendation has to name what becomes actionable, not just count risks.** First identify why the ticket is an 8: *risk-stacked* (driven by stacked risk dependencies) or *breadth-driven* (mechanical scope, no risk dependency). For a risk-stacked 8, split only when some resulting piece clears two gates: it's durable (its logic either never touches the unresolved surface, or only its call site would need rework if that surface shifts—not its core design) and material (that durable piece would be at least a 2 on its own, not a 1-point stub). Cutting a two-risk 8 into two one-risk pieces that are both still gated on the exact same unresolved thing doesn't clear the durability gate—that's relabeling the wait with smaller numbers, not reducing it. A durable piece too small to be its own ticket becomes a prep-work note instead of a split. For a breadth-driven 8, actionability is beside the point (nothing was blocked); split only along a genuine vertical boundary—a business-rule or data variation each piece could ship and review on its own—never an arbitrary chunk of the same work. Reviewability, parallelizing across engineers, or a PM milestone are real but separate reasons to cut up a ticket; when the ticket's own structure surfaces one, it's called out as a process note that never changes the number.

## Company riders

If a client's own pointing scale isn't Fibonacci, a sibling `SKILL.<company>.md` file (not synced publicly) can define a mapping to a different scale—e.g., a 1/3/10/30/100 scale with 100 as the split threshold. Estimating still happens against the five canonical tiers above and their anchors, split tests, and reasoning; only the final number is translated into the client's scale at output time, so the rubric itself never has to be reinterpreted per client.

---

## Feedback

This repo is a one-way sync mirror of a private source; it isn't set up to accept pull requests. If you spot a bug or have a suggestion, please open an issue instead.

## License

This skill is licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

## Acknowledgments

- [The Humanizing Work Guide to Splitting User Stories](https://www.agileforall.com/patterns-for-splitting-user-stories/)
- Tech Lead Handbook, [Feature slicing](https://techleadhandbook.org/agile/feature-slicing/)
- Bill Wake, [Twenty Ways to Split Stories](https://xp123.com/articles/twenty-ways-to-split-stories/)
- Mike Cohn, [SPIDR: Five Simple but Powerful Ways to Split User Stories](https://www.mountaingoatsoftware.com/agile/five-simple-but-powerful-ways-to-split-user-stories)
- <https://github.com/afbreilyn/afb-tdd>
- <https://github.com/github/spec-kit>
- <https://github.com/ianmcnally/code-reviewer>
- <https://github.com/kenjudy/pdca-framework>
- <https://gitlab.com/phillippitts/agent-professional-review-pipeline>
