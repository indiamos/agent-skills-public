# story-retro

Retrospective analysis of completed tracked tickets — what went well, what didn't, and what to carry forward.

## Context

Rather than reconstructing what happened from memory, this skill pulls the actual ticket history, linked PRs, and review comments to build a timeline. Useful for performance review evidence, post-incident write-ups, or just closing the loop on a complicated ticket.

Supports Jira and Linear today (see `trackers/jira.md` and `trackers/linear.md`) — the active
tracker is auto-detected from which tracker's MCP is connected, so there's nothing to configure
when switching between client engagements. Add a `trackers/{tracker}.md` file to support another
tracker (see `AGENTS.md`'s "Ticket-tracker sub-files" section for the convention).

## Usage

```
/story-retro [ticket-id-or-url]
```

Pulls the ticket history, linked PRs, and comments to produce a structured retrospective: timeline, blockers, surprises, and actionable takeaways.

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
