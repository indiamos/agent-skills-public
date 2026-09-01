# commit-plan

Plan and organize uncommitted changes into a logical commit series before pushing.

## Context

The common alternative — asking Claude to "help me commit" mid-session — means Claude starts writing commits before you've agreed on how the changes should be grouped. This skill does the analysis first, proposes a full commit series, and waits for approval before writing a single commit.

Especially useful on branches with a lot of heterogeneous changes where the right grouping isn't obvious.

## Usage

```
/commit-plan
```

Analyzes unstaged and staged changes, groups them into coherent commits with conventional commit messages, and presents the plan for review before writing anything.

## Configuration

| Env var | Purpose | Default |
| --------- | --------- | --------- |
| `COMMIT_PLAN_OUTPUT_DIR` | Directory where the planning file is saved | current working directory |

Set in your Claude settings (`~/.claude/settings.json` or `.claude/settings.local.json`):

```json
{
  "env": {
    "COMMIT_PLAN_OUTPUT_DIR": "~/ai-context/commit-plans"
  }
}
```

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
