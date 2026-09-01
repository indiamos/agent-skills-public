# review-claude-md

Review recent project changes and suggest updates to keep the project's CLAUDE.md accurate and useful.

## Context

CLAUDE.md files drift. You add a library, rename a service, change a convention — and the file doesn't get updated. This skill looks at recent commits and diffs them against the current CLAUDE.md to surface specific stale sections, documentation gaps, and things that are documented but no longer true.

## Usage

```
/review-claude-md
```

Looks at recent commits, new files, and changed patterns to identify CLAUDE.md sections that are stale, missing, or worth adding. Produces specific edit suggestions rather than a generic list.

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
