# pr-scout-ask

Convert a PR Scout review file into question-framed comments — rewriting findings as respectful questions rather than assertions.

## Context

A companion to `/pr-scout`. PR Scout produces findings in declarative form ("this function has no error handling"). This skill rewrites them as questions ("Have you considered adding error handling here?"). Useful when you want to post AI-generated review comments but want them to feel collaborative rather than authoritative — especially with authors who respond better to questions than to statements.

## Usage

```
/pr-scout-ask [path-to-review-file]
```

Takes the Markdown review file produced by `/pr-scout` and rewrites its findings as questions you could post directly as review comments. Pairs with `/pr-scout`.

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
