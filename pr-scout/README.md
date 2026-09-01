# PR Scout

**_A code review skill that doesn't get on your last damn nerve._**

PR Scout is intended to be pretty fast, pretty accurate, and optimized for human oversight, but also to NOT need you to babysit it through 200 tool calls that each require fingerprint authentication.

## Context

Unlike most AI review tools, this one doesn't post to GitHub automatically. It writes a local Markdown file for you to read and filter first, because posting a review comment is a social act — tone, relationship, and context all matter in ways AI can't assess. See **Key differences from other PR review tools** below for the full rundown.

Companion skill: `/pr-scout-ask` rewrites findings as questions if you'd rather post them in a less assertive tone.

## Usage

```
/pr-scout <PR-number-or-URL> [file:output-path.md]
```

- If you omit the path, `pr-scout` will default to saving a timestamped file in your current directory.
- Pass `github` instead of a file path to use GitHub posting mode (you'll still be prompted before anything is sent).
- Agree to check commits, when prompted, if you want commit message style feedback included in the review. This defaults to no, since you might have commit message rules in your personal AI settings that are not shared by the team or code owners.

## Configuration

| Env var | Purpose | Default |
| --------- | --------- | --------- |
| `PR_SCOUT_DEFAULT_OUTPUT` | Default output mode: `file` or `github`; skips the output-mode prompt | (ask each time) |
| `PR_SCOUT_OUTPUT_DIR` | Directory where review files are saved | current working directory |

Set in your Claude settings. Project-level values override user-level; `.local.json` overrides `.json`:

- `~/.claude/settings.json` (user-level)
- `.claude/settings.json` in a project directory (project-level)
- `.claude/settings.local.json` in a project directory (project-local, highest precedence)

```json
{
  "env": {
    "PR_SCOUT_DEFAULT_OUTPUT": "file",
    "PR_SCOUT_OUTPUT_DIR": "~/ai-reviews"
  }
}
```

When `PR_SCOUT_DEFAULT_OUTPUT` is set, the output-mode prompt is skipped — but two guards remain in place:

- **File mode**: if a file already exists at the computed path, you'll be asked to confirm before it's overwritten (or enter a different path).
- **GitHub mode**: step 8 still shows you a full preview and asks for confirmation before posting.

## Key differences from other PR review tools

### _You_ decide which comments to post

Most AI review tools assume you want them to post comments directly to GitHub on your behalf. This one doesn't. The default output is a local Markdown file so that you the reviewer can decide what (if anything) to post.

Why be so picky?

- AI may not have context on the PR author's decisions that you do.
- AI is lousy at balancing its tone between know-it-all-ism and obsequiousness.
- Posting a comment on someone else's PR is a social act, not just a technical one, and how you comment is usually influenced by your relationship with the PR author, which AI knows nothing about. Maybe they're very thick-skinned and don't care what you say; maybe they lack confidence in their code and you want to encourage them; maybe they're defensive and you don't want to set them off.

So you should be able to read the findings first, decide which ones you agree with and which are noise, consider whether they are worded appropriately, and then post comments you can actually stand behind.

See also the companion skill `/pr-scout.ask`, which tries to reframe AI's typical know-it-all comments as respectful questions!

**Note:** GitHub posting is still an option, if you're feeling lucky or don't care whether you toss your relationship with the PR author directly into the bin. Just pass `github` instead of an output file path when you invoke the skill.

### You can see findings Claude is not so sure about

This skill runs six specialist agents (bugs, `CLAUDE.md` compliance, git history, previous comments, code comments, struct invariants) and then scores every finding with a separate Haiku agent. Some skills will filter out any comment the agent is less than 80% sure of, and they will never show you the others unless you ask for the deep cuts.

But 65 is a passing grade in NYC public schools, so that's the cutoff PR Scout uses! _You_ decide whether to play a hardass teacher.

### You _can_ nitpick over commit messages, but it assumes you don't want to

If a repo's owners really care about commit message style, they probably set up a pre-commit hook for it. Never encountered this? That's because most devs don't care _that_ much. But maybe they cared enough to mention in the `CLAUDE.md` file that they follow [Conventional Commits](https://www.conventionalcommits.org/) minus scopes, and you want to make sure the preference is being respected. Maybe you want to check commit message style only on your own PRs but not police others'.

PR Scout checks that proposed changes adhere to `CLAUDE.md` and a [spec-kit](https://github.com/github/spec-kit) constitution file, if the repo has one. That would also include enforcing any commit message preferences that those files contain. Instead, PR Scout skips such rules unless you opt in.

### If GitHub MCP isn't working, PR Scout asks whether you want to continue

As you might imagine, PR review skills make a lot of requests to GitHub, both from the main conversation and from subagents—_dozens_ of them, if not _hundreds_. Without an MCP, every GitHub read operation falls back to either `gh` CLI or bash-wrapped `git` commands. If either of those methods is used, you may get an SSH fingerprint prompt for _every single one of them_. That's extremely annoying, and it's hard to interrupt once those subagents get going. PR Scout stops to give you a chance to fix the MCP issue.

### You can review draft PRs

If you want to check a draft PR for problems, PR Scout will help you. Isn't that one of the main reasons for making a draft in the first place? Why would a review tool spurn drafts?!

### You can re-review PRs

Some skills quit if you've already left a review on the PR. PR Scout doesn't assume you're some swoop-and-pooper who ignores revisions.

### If an issue has already been called out, PR Scout tells you

The skill gives you a heads-up; you decide whether to dogpile.

### It peels apart palimpsestic bot comments

Many automated PR review tools can't thread conversations with the author but instead revise a single comment on every run, to avoid cluttering the conversation. Such revisions are not obvious in Github's UI, which makes it hard to tell whether the author made changes in response to an earlier version of that comment. PR Scout looks at the history of any comment authored by a bot, so that it can get the whole story.

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
