# catalog-instruction-patterns

Extract and catalog reusable instruction patterns from skill files to inform writing or improving skills.

## Context

Skill authoring often happens by feel — you write what seems clear and iterate. This skill makes the implicit explicit: it reads your existing skills, extracts recurring structural patterns (STOP gates, state binding, output format specs, skip rules), and names them. The resulting catalog is what `/improve-skill` uses as its rubric.

Run it whenever you've significantly added or revised skills to keep the catalog current.

## Usage

```
/catalog-instruction-patterns [path-to-skills-dir]
```

Scans skill files in the given directory, extracts named patterns (STOP gates, state binding, output format specs, skip rules, etc.), and writes a catalog file you can use with `/improve-skill`.

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
