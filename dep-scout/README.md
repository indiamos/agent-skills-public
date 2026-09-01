# Dep Scout

**_Traffic-light safety verdicts for dependency-bump PRs._**

`dep-scout` reviews dependency-bump PRs and answers the question a rotating support engineer actually needs: "Is this safe to merge?" It handles bot-authored PRs (dependabot, renovate), human-authored security fixes, and mixed PRs where a bot opened the PR and a human later revised it.

## Usage

```
/dep-scout <PR-number-or-URL> [file:output-path.md] [github]
```

- Pass a bare PR number when invoked from the repo directory: `/dep-scout 449`
- Pass a full URL or `owner/repo#number` from any directory: `/dep-scout indiamos/my-api#449`
- Pass `file:<path>` to write to a specific path; omit to use the configured default or be prompted.
- Pass `github` to post as a PR comment (you'll be asked to confirm before anything is sent).

## Configuration

| Env var | Purpose | Default |
|---------|---------|---------|
| `DEP_SCOUT_OUTPUT_DIR` | Directory where review files are saved | (falls back to `PR_SCOUT_OUTPUT_DIR`, then prompts) |
| `DEP_SCOUT_DEFAULT_OUTPUT` | Default output mode: `file` or `github`; skips the output-mode prompt | (ask each time) |
| `PR_SCOUT_OUTPUT_DIR` | Fallback output directory (shared with pr-scout) | (prompts) |

Set in your Claude settings. Project-level values override user-level; `.local.json` overrides `.json`:

- `~/.claude/settings.json` (user-level)
- `.claude/settings.json` in a project directory (project-level)
- `.claude/settings.local.json` in a project directory (project-local, highest precedence)

```json
{
  "env": {
    "PR_SCOUT_OUTPUT_DIR": "~/ai-reviews"
  }
}
```

If you already have `PR_SCOUT_OUTPUT_DIR` set for `pr-scout`, `dep-scout` will use the same directory automatically.

## What it checks

For each bumped package:

- **Changelog** between old and new version (GitHub releases, CHANGELOG.md, or registry page)
- **Breaking changes** — flagged from changelog keywords and breaking API search in the consuming repo
- **Security fixes** — CVE IDs and advisories (Dependabot alert page used as primary source if available)
- **Traffic-light verdict** — 🟢 safe / 🟡 review / 🔴 do not merge

Plus shared checks:

- **CI status** — check run results for the PR head commit
- **Security scanner** — detects Wiz scanner summary comments and their edit history (so you can see if issues were originally flagged and later resolved)

## Supported ecosystems

- Go modules (`go.mod`)
- Ruby gems (`Gemfile`)
- npm/yarn (`package.json`, `yarn.lock`, `package-lock.json`)

## Output format

Reviews are written as Markdown files (default) or posted as GitHub PR comments. The default output location is the same directory as `pr-scout` reviews, so all your AI reviews land together.

## License

This skill is licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
