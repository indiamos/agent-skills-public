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
| 8 | Multiple unresolved external decisions, infra blast radius, or several independent *risk* dependencies stacked together; flag for splitting into smaller slices. |

Every estimate includes why that number was chosen and not the ones adjacent to it.

**Dependencies only count if they're a genuine risk, not just a wait.** A dependency whose shape is already fully defined and just hasn't merged/landed yet is *sequencing*—it's a scheduling fact, not a complexity fact, and doesn't raise the score no matter how many of them stack up. A dependency whose contract, spec, or decision is still unsettled is *risk*, and that's what actually earns a 5 or 8. Both kinds are still listed in the Dependencies section for planning purposes; sequencing ones are just called out as not affecting the number.

---

## Feedback

This repo is a one-way sync mirror of a private source; it isn't set up to accept pull requests. If you spot a bug or have a suggestion, please open an issue instead.

## License

This skill is licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

## Acknowledgments

- <https://github.com/afbreilyn/afb-tdd>
- <https://github.com/github/spec-kit>
- <https://github.com/ianmcnally/code-reviewer>
- <https://github.com/kenjudy/pdca-framework>
- <https://gitlab.com/phillippitts/agent-professional-review-pipeline>
