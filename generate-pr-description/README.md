# generate-pr-description

A Claude Code skill that analyzes a feature branch and produces a clear, neutral, reviewer-friendly PR description.

## Context

Rather than relying on your verbal summary, this skill reads the actual diff and fetches the linked ticket to produce a description grounded in what the code actually changed. The local-override pattern in the README shows how to extend it with project-specific title formats without forking the skill.

## How to use

### Global — use as-is

This skill lives in `~/.claude/skills/generate-pr-description/` and is available in every Claude Code session. Invoke it with `/generate-pr-description` (or `/generate-pr-description <branch-name>` or `/generate-pr-description <GitHub tree URL>`) from any project.

### Configuration

The skill is issue-tracker-agnostic. Set these in the `env` object of `~/.claude/settings.json` (user-level), or `.claude/settings.json` / `.claude/settings.local.json` in the current directory or any of its ancestors up to your home directory (project-level — checked outermost-first, so a config closer to the current directory wins). This means a `.claude/settings.json` on a parent folder that contains several repos (e.g., `~/repos/acme/.claude/settings.json`) is picked up automatically by every repo nested inside it, without needing its own copy:

```json
{
  "env": {
    "BASE_TICKET_URL": "https://linear.app/acme/issue/",
    "TICKET_LABEL": "Linear",
    "PR_DESC_OUTPUT_DIR": "~/ai-context/pr-descriptions",
    "PR_DESC_DEFAULT_OUTPUT": "file"
  }
}
```

- `BASE_TICKET_URL` / `TICKET_LABEL` — build the ticket link (works for Linear, Jira, Shortcut, GitHub Issues, or anything else with a predictable URL shape). Omit `BASE_TICKET_URL` to skip the ticket link entirely.
- `PR_DESC_OUTPUT_DIR` / `PR_DESC_DEFAULT_OUTPUT` — write the finished description to a markdown file instead of (or in addition to prompting for) printing it in chat. Pass `file:<path>` as a skill argument to override per-invocation.

### Local — inherit and extend with your own project conventions

For a project with its own PR title format, issue tracker link style, or repo-specific routing rules, create a local skill that delegates to this one and adds project-specific overrides:

```markdown
---
name: generate-pr-description
description: Generate a PR description for this project.
user-invocable: true
---

Follow the PR description workflow defined in [~/.claude/skills/generate-pr-description/SKILL.md](~/.claude/skills/generate-pr-description/SKILL.md).

## Project-specific title format

**If the repo is `neon-dash` or `neonmoose`:** use Conventional Commits format — `neon-dash` has a CI check (`amannn/action-semantic-pull-request`) that fails on non-conforming titles; `neonmoose` uses the `feat:` prefix in `version_bump.yml` to determine minor vs patch releases.

    <type>: <Imperative summary> [TICKET-###]

**All other repos (including `advisor`):** use the bracket format:

    [TICKET-###] <Imperative summary of the main action>

✅ `[TICKET-1063] Use plan type to resolve FEIN ties in company lookup`
❌ `fix: use plan type to resolve FEIN ties [TICKET-1063]` — commit message style; ticket ID belongs at start
❌ `[TICKET-1063] Improve company lookup logic.` — "Improve" is a prohibited word; trailing punctuation

## Project-specific output structure

Ticket link format is handled by `BASE_TICKET_URL` / `TICKET_LABEL` (see Configuration above). No per-project override is needed unless the link shape is unusual.

## Additional checklist items

- [ ] Title follows `[TICKET-###]` format for non-Conventional-Commits repos, imperative, no trailing punctuation
- [ ] Ticket link is present and correct
```

The local skill inherits the full workflow and adds only what differs. `/generate-pr-description` in that project runs the local version automatically.

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
