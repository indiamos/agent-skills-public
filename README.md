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

This is a subset of a larger private skill collection that I use for everyday software development work as a consultant. Each skill here is self-contained (its own `SKILL.md`, `README.md`, `LICENSE`, and `CHANGELOG.md`) and _somewhat_ intended for use outside of any specific company or team. See each skill's own `README.md` for usage details and configuration.

### The context these skills were built in

I've worked at a small agile software consultancy since 2018, and I'm often—though not always—an outsider to the team, department, or company I'm working with. That shapes these skills in a few ways:

- **Convention over invention.** My bias is toward following a team's existing conventions unless I have a good argument for deviating. Several skills (e.g., `mine-pr-conventions`, `review-claude-md`) exist specifically to surface those conventions rather than assume my own.
- **Commit history as documentation.** I err on the side of documenting decisions in commit messages, since I probably won't be around later when questions come up. `commit-message` and `commit-plan` reflect that.
- **No architectural authority.** I'm rarely in a position to make high-level architecture calls—consultants usually get hired to work within an existing codebase, or to build a discrete piece that fits into a larger system that's already well established. Nothing here assumes you're a primary system architect or tech lead; these are oriented toward the experienced individual contributor.
- **Portable over personal.** I usually work for one client at a time, but sometimes for a very short time. Sometimes I'm on hardware they supply, and sometimes on my consultancy's, so although I'm very opinionated about _some_ tools (it's extremely inefficient for me to use any IDE besides VSCode, at this point), a setup that travels well matters more to me than one that's deeply customized to a single machine or stack.
- **Generalist, not specialist.** I switch tech stacks regularly, so you won't find much that's language-specific here. That said, most of these skills were drafted while I was working at a single client, and few have yet been extensively battle-tested outside that environment.

### Why these skills don't write your words for you

I was an English major in college, and before I was a developer, I worked in and around publishing for years, writing both prose and code in a lot of non-technical contexts. I have strong opinions about language and how it's written, so most of these skills are deliberately built to _not_ post comments, reviews, issues, or PR descriptions on my behalf unless I explicitly ask them to.

I also distrust AI more than I trust it, but I can't really choose not to use it, given the nature of my work. I've seen enough lousy AI-generated code in the stacks I know well to be certain that it's producing _at least_ that much trash in those stacks where I'm not equipped to catch the errors myself. So these skills assume there's a cautious human in the loop, reading everything with real skepticism, even if not always with real expertise.

Speaking of caution…

## Warning: You get what you pay for

These skills work well for me, but I can't promise they're safe for everyone. A few things worth knowing before you use them:

- **Read the skill and any accompanying scripts before running them.** Skills can write files, run shell commands, post to external APIs, and make other changes to your environment. You should know what a skill does before handing it the keys.
- **I work with a fairly long `deny` list and use Claude's auto mode only sparingly.** I require a human in the loop for most consequential actions (e.g., `rm -rf`—but also `git push`), so some of these skills may be less careful than you'd want in a more permissive setup.
- **No warranty.** These are personal tools shared in good faith. They could wreck your code, your config, or your day. Use them at your own risk.

## License

Each skill is individually licensed; see its accompanying `LICENSE` file. Most are [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

## Feedback

This repo is a one-way sync mirror of a private source; it isn't set up to accept pull requests. If you spot a bug or have a suggestion, please open an issue instead, and I'll consider folding it into the source.
