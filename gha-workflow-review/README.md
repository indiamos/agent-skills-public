# gha-workflow-review

A Claude Code skill that reviews GitHub Actions workflow files for common migration and correctness issues.

## Context

When repos migrate from CircleCI to GitHub Actions, the infra-team migration is typically scoped to the deploy pipeline — tests, notification completeness, and deploy gating details are often left for the app team to verify. This skill encodes the patterns that have repeatedly needed fixing after migrations across several Go services after CircleCI→GHA migrations.

## Usage

```sh
/gha-workflow-review
```

Run from the repo root. The skill reads all files in `.github/workflows/` and works through a seven-category checklist, then produces a structured report of findings.

---

## Feedback

This repo is a one-way sync mirror of a private source; it isn't set up to accept pull requests. If you spot a bug or have a suggestion, please open an issue instead.

## License

This skill is licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
