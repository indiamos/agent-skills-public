# review-plan

Audit a multi-task implementation plan for commit-mechanics gaps before execution begins, and draft concrete rewrites to close them.

## Context

A plan that says "commit after each task" often still gets executed as one giant batch, because the commit policy was implied by the task structure rather than stated as a hard gate — leaving someone to unwind the working tree and reapply the diff by hand into per-task commits after the fact. This skill checks a plan's text against a checklist of the specific gaps that cause that failure mode (missing blocking gates, an unstated commit convention, no fixup-vs-fix-forward policy, unstated authorization, no ask-before-worktree step, no completion self-check) and drafts exact replacement text for each gap it finds.

Companion skill: `commit-plan` performs the after-the-fact reconstruction; this skill exists to make that reconstruction unnecessary.

## Usage

```
/review-plan <path-to-plan-file>
```

Reads the plan, checks it against an eleven-item checklist, and — if any item fails — presents the full checklist plus drafted rewrites for review. Nothing is written until you approve (`yes` / `no` / `select`).

If the plan is single-task or produces no committed changes, the skill reports that the check doesn't apply and halts.

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
