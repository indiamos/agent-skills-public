# cross-check-review

Assess a pr-scout review to decide which findings are worth flagging to the PR author — or, if the PR is yours, receive the review instead.

## Context

Running `/superpowers:receiving-code-review` on someone else's PR requires manually prefacing the command with "Not my PR; I'm just assessing whether to flag these issues to the author:" to avoid Claude trying to implement the fixes. This skill wraps that workflow: it detects the PR author automatically and adopts the right perspective without any manual framing.

**Prerequisite:** `superpowers:receiving-code-review` from the [obra/superpowers](https://github.com/obra/superpowers) repo. This skill invokes it directly and will fail without it.

Companion skills: `/pr-scout` produces the review; `/pr-scout-ask` rewrites findings as questions if you'd rather post them in a less assertive tone.

## Usage

```txt
/cross-check-review
```

Invoke after running `/pr-scout`. The skill determines the PR author from context and branches:

- **PR is yours** — invokes `superpowers:receiving-code-review` and follows it exactly.
- **PR is someone else's** — enters Assessor mode: verifies each finding and outputs a verdict for each one. Does not suggest implementing anything.

### Assessor mode verdicts

| Verdict | Meaning |
| ------- | ------- |
| **Flag** | Technically valid — worth raising with the author |
| **Skip** | Incorrect, inapplicable, or YAGNI |
| **Unclear** | Can't verify without more context — explains what was checked and what remains unresolved |

Before flagging any finding, the skill checks whether the concern is actually reachable (call sites, guards, invariants). Speculative language — "could", "might", "it appears" — is a signal to verify first, not to flag. Open questions about fix strategy or design belong to the PR author, not to you.

---

## Feedback

If you make improvements to this skill, feel free to fork the repo and open a PR.

## License

This skill is licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
