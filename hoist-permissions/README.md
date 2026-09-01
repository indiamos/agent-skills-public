# hoist-permissions

Run the permissions hoister script and report what Claude Code permissions were promoted from project-level to user-level settings.

## Context

Claude Code's permission model lets permissions be granted at the user level or the project level. It's easy to accumulate the same permission granted repeatedly across many projects, or to set a permission only for a subproject when you want it to be global. This skill runs the hoister script and surfaces what was promoted, so you can audit the result and decide what belongs at the user level permanently. It **DOES NOT** update `~/.claude/settings.json` for you.

## Usage

```txt
/hoist-permissions
```

Invokes the hoister, summarizes which permissions were moved, and flags anything unexpected.

## Configuration

| Env var | Purpose | Default |
| --------- | --------- | --------- |
| `HOIST_PERMISSIONS_ROOTS` | Comma-separated list of root directories to scan. Tilde expansion is supported. | `~/.claude,~/repos` |
| `HOIST_PERMISSIONS_SKIP` | Comma-separated list of paths to exclude from the scan. Folder entries skip everything under them; file entries skip only that file. Tilde expansion is supported. | (no skips) |

Set in `~/.claude/settings.json` at the user level:

```json
{
  "env": {
    "HOIST_PERMISSIONS_ROOTS": "~/.claude,~/work/repos,~/personal/repos",
    "HOIST_PERMISSIONS_SKIP": "~/.claude/plugins/, ~/work/repos/some-project/.claude/settings.json"
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
