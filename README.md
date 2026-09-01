# agent-skills

A collection of [Claude Code](https://claude.com/claude-code) skills I've used in my work as a lead consulting software developer. Use them as-is or as a reference for writing your own.

## Skills

| Skill | Description |
| --- | --- |
| [`catalog-instruction-patterns`](catalog-instruction-patterns) | Extract reusable patterns from skill files |
| [`commit-message`](commit-message) | Generate a conventional commit message from a diff |
| [`commit-plan`](commit-plan) | Plan and organize uncommitted changes into a logical commit series |
| [`cross-check-review`](cross-check-review) | Assess a pr-scout review to decide which findings are worth flagging to the PR author |
| [`dep-scout`](dep-scout) | Traffic-light safety verdict for dependency-bump PRs |
| [`estimate-tickets`](estimate-tickets) | Estimate tickets on a Fibonacci scale, flagging grooming items and undeclared dependencies |
| [`export-full`](export-full) | Export a conversation to a readable transcript |
| [`generate-pr-description`](generate-pr-description) | Generate a structured PR description from a branch diff and its tracked ticket |
| [`gha-workflow-review`](gha-workflow-review) | Audit GitHub Actions workflow files for common migration and correctness issues |
| [`granola-notes`](granola-notes) | Fetch meeting notes and transcripts from Granola via its REST API |
| [`hoist-permissions`](hoist-permissions) | Run the permissions hoister script |
| [`improve-skill`](improve-skill) | Audit and improve a skill file |
| [`mine-pr-conventions`](mine-pr-conventions) | Discover coding conventions from a repo's PR review history |
| [`pr-scout`](pr-scout) | Thorough parallel code review of a PR |
| [`pr-scout-ask`](pr-scout-ask) | Convert a pr-scout review file into question-framed comments |
| [`review-claude-md`](review-claude-md) | Review recent changes and suggest CLAUDE.md updates |
| [`story-retro`](story-retro) | Retrospective analysis of completed tracked tickets (Jira, Linear) |

## Installing a skill

This repo is also a Claude Code plugin marketplace (`indiamos-skills`), so the easiest way to install a skill is:

```sh
/plugin marketplace add indiamos/agent-skills-public
/plugin install pr-scout@indiamos-skills
```

(swap `pr-scout` for any skill name from the table above). `/plugin marketplace update` and Claude Code's normal auto-update pick up changes automatically — there's no version to bump.

`improve-skill` depends on `catalog-instruction-patterns` and installs it automatically. Every other skill installs independently, though a few work well together — `pr-scout` and `pr-scout-ask` are a natural pair (see each skill's own README) even though installing one doesn't require the other.

### Manual install (no plugin system)

Claude Code also discovers skills one level under `~/.claude/skills/` (i.e., `~/.claude/skills/<name>/SKILL.md`), if you'd rather not use the plugin system:

```sh
git clone https://github.com/indiamos/agent-skills-public.git /tmp/agent-skills-public
cp -r /tmp/agent-skills-public/<skill-name> ~/.claude/skills/<skill-name>
```

Or clone the whole repo somewhere and symlink individual skills into `~/.claude/skills/` so you can `git pull` updates later.

## About this repo

This is a subset of a larger private skill collection that I use for everyday software development/consulting work. Each skill here is self-contained (its own `SKILL.md`, `README.md`, `LICENSE`, and `CHANGELOG.md`) and _somewhat_ intended for use outside of any specific company or team. See each skill's own `README.md` for usage details and configuration.

## A word of caution

These skills work well for me, but I can't promise they're safe for everyone. A few things worth knowing before you use them:

- **Read the skill and any accompanying scripts before running them.** Skills can write files, run shell commands, post to external APIs, and make other changes to your environment. You should know what a skill does before handing it the keys.
- **I work with a fairly long `deny` list and rarely use Claude in auto mode.** That means I have a human in the loop for most consequential actions, and some of these skills may be less careful than they need to be for a more permissive setup.
- **No warranty.** These are personal tools shared in good faith. They could wreck your code, your config, or your day. Use them at your own risk.

## License

Each skill is individually licensed; see its accompanying `LICENSE` file. Most are [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

## Feedback

This repo is a one-way sync mirror of a private source — it isn't set up to accept pull requests. If you spot a bug or have a suggestion, please open an issue instead and I'll fold it into the source.
