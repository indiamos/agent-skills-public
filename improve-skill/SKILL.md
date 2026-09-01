---
name: improve-skill
description: Use when you want to audit an existing skill or command file against the instruction pattern catalog — vague skip criteria, missing STOP gates, absent output format specs, undefined scoring rubrics, no preview-before-write step.
---

# Improve Skill

## Overview

Audit a skill or command file against the instruction pattern catalog and produce specific, pattern-named rewrites. The output is a list of concrete proposals — each tied to a named pattern, each with a rewritten version ready to apply.

## Step 0 — Bind inputs before any other action

Read the arguments provided when the skill was invoked.

- **target** — path to the skill or command file to improve

**STOP gate:** If no target file was provided, ask: "Which skill or command file should I improve? Please provide a file path." Wait for a response before continuing.

**Resolve the pattern catalog path:**

Read the following files in order using the Read tool. For `IMPROVE_SKILL_CATALOG_PATH`, the last file that defines it wins. Do not use Bash or `printenv` — env vars are not reliably injected into skill context.

1. `~/.claude/settings.json` (user-level)
2. `.claude/settings.json` relative to CWD (project-level, if it exists)
3. `.claude/settings.local.json` relative to CWD (project-local, if it exists)

If any file exists and its `env` object contains `IMPROVE_SKILL_CATALOG_PATH`, store that value as CATALOG_PATH. If no file defines it, use the default: `~/.claude/skills/improve-skill/instruction-patterns.md`.

**If the file at CATALOG_PATH does not exist:**

- Tell the user: "The instruction pattern catalog was not found at `<CATALOG_PATH>`. I need to generate it first by running `/catalog-instruction-patterns` on your skills directory."
- Invoke the `catalog-instruction-patterns` skill, passing `~/.claude/skills` as the source directory, and ask the user to save the output to CATALOG_PATH before continuing.
- **STOP** until the user confirms the catalog file has been saved, then re-read it.

To use a custom catalog location, set `IMPROVE_SKILL_CATALOG_PATH` in your Claude settings. Project-level values override user-level; `.local.json` overrides `.json`:
```json
{
  "env": {
    "IMPROVE_SKILL_CATALOG_PATH": "~/.claude/skills/improve-skill/instruction-patterns.md"
  }
}
```

Read both files before proceeding:

1. The target file at `TARGET`
2. The pattern catalog at `CATALOG_PATH`

**STOP gate:** If either file cannot be read, report which file failed and halt.

Carry `TARGET` and the full content of both files through all remaining steps.

---

## Step 1 — Inventory existing patterns

**Precondition:** Both files are loaded.

For each numbered step and named section in the target file, identify which patterns it currently uses. Record:

```
[STEP] Step N / section heading
[PATTERNS PRESENT] comma-separated list, or "none"
[NOTES] any observations about how well each pattern is applied
```

Use only these pattern names: Argument binding, Command binding, Precondition annotation, STOP gate, Conditional routing, Parallel dispatch, Scoring rubric, Output format spec, Preview-then-confirm, Skip rule, Annotation tagging, File-conditional.

---

## Step 2 — Identify gaps and misapplications

**Precondition:** Pattern inventory from Step 1 is complete.

For each step from Step 1, check for the following:

**Missing patterns that should be present:**

- A step that reads a value from arguments — does it have Argument binding with a STOP gate for the absent case?
- A step that runs a tool call — does it have Command binding with an explicit halt-on-failure clause?
- A step that could produce two or more meaningfully different behaviors — does it have Conditional routing or a STOP gate?
- A step that asks the agent to omit or exclude items — does it have an explicit Skip rule, or does it use vague idioms instead?
- A step that produces a structured artifact — does it have an Output format spec with ✅/❌ examples?
- A step that ranks, weights, or signals confidence — does it have a Scoring rubric with labeled levels and boundary criteria?
- A step that writes to a file or posts to an external system — does it have Preview-then-confirm?
- A step that dispatches multiple agents — does the agent list use a table or explicit `<use_parallel_tool_calls>` directive (not an `a.`/`b.`/`c.` ordered list)? Does each agent produce a complete, self-contained artifact (fully-formed URLs, not partial references requiring a follow-up fetch)? Are agents prohibited from re-running tool calls already executed in prior steps? Are the sub-tasks genuinely independent (no shared state, no dependency on each other's output)?

**Misapplied patterns:**

- STOP gate with a vague or subjective condition rather than a specific, testable one
- Skip rule that uses idioms ("rubber-stamp", "trivial", "low quality") instead of explicit, enumerable criteria
- Output format spec with no ✅/❌ examples
- Scoring rubric with unlabeled levels or undefined level boundaries
- Conditional routing with only one meaningful path (should be a STOP gate instead)
- Parallel dispatch written as an ordered list (`a.`, `b.`, `c.`) rather than a table or with an explicit `<use_parallel_tool_calls>` directive — LLMs interpret ordered lists as sequential steps
- Parallel dispatch agents that call tools already called in prior steps — creates inconsistency and redundant work; unverifiable cases belong in the scoring rubric's lower confidence tiers, not re-fetched
- Does any agent constraint use an exception clause ("do not do X, except when Y")? Rewrite as a Conditional routing gate instead — the exception becomes a branch, not a carve-out from a prohibition:
  ❌ "Must not run shell commands. The only permitted reads are config files."
  ✅ "If the issue is flagged as a config violation, read the config file to verify. Otherwise, return your result immediately without calling any tools."

**YAML frontmatter:**

- Does the description summarize the skill's workflow rather than its triggering conditions? A workflow-summarizing description causes agents to follow the description instead of reading the body.

Record each gap or misapplication:

```
[STEP] Step N / section heading
[ISSUE] One sentence: what is wrong or missing
[PATTERN] Which pattern should be applied or corrected
[SEVERITY] High — significantly reduces determinism or correctness
            Medium — reduces clarity; a skilled author would notice
            Low — minor polish
```

**STOP gate:** If no issues are found, report "No issues found — skill follows all applicable patterns." and halt.

---

## Step 3 — Propose rewrites

**Precondition:** Issues list from Step 2 is complete.

For each High and Medium issue, produce a specific rewrite in this format:

**Rewrite N of M** — Step N, section heading · *Pattern name · Severity*

**Replace:**

```
verbatim current text (or paraphrase if over 60 words, with generic placeholders)
```

**With:**

```
rewritten instruction using the pattern correctly
```

---

Use the canonical examples in `instruction-patterns.md` as structural templates — replace their domain-specific content with the actual content of the target skill.

Two principles that improve rewrite quality:

- **Positive framing over negative**: Write what the step must produce ("return a fully-formed GitHub link") rather than what it must not do ("do not return partial references"). Negative framing is less reliable; positive framing specifies the success condition.
- **Include the "why" for constraints**: Bare prohibitions are less reliably followed than prohibitions with a brief stated reason. Append it in the same line as the constraint — one clause is enough: "do not do Z — because Y." Do not write a separate explanatory paragraph.

Do not propose rewrites for Low severity issues unless the user asks.

✅ CORRECT:

**Rewrite 1 of 3** — Step 2, skip rule · *Skip rule · Medium*

**Replace:**

```
Skip praise-only approvals.
```

**With:**

```
Skip PRs whose only review content is approvals with no comment body
or comments consisting solely of: "LGTM", "looks good", "nice work",
"ship it", ":+1:", "👍", or equivalent.
```

❌ WRONG — **Rewrite 1 of 3** — Step 2, skip rule · *Various · Medium*

**Replace:**

```
The step is unclear.
```

**With:**

```
Make it clearer.
```

(Too vague — no specific pattern named, no actionable rewrite, proposed text is not a real instruction)

---

## Step 4 — Present and confirm

Output the following in full — do not summarize, paraphrase, or abbreviate any part:

1. The complete Step 2 issues table (all severities)
2. Every Step 3 proposed rewrite in full, including `[CURRENT TEXT]` and `[PROPOSED TEXT]`

Then, as the final line of output, ask:

> Should I apply these changes to `TARGET`? (yes / no / select)
> - **yes** — apply all High and Medium rewrites
> - **no** — halt; leave the file unchanged
> - **select** — list each rewrite numbered; wait for the user to specify which to apply by number

Do not write to any file until the user responds. If running as a subagent, the invoking agent MUST relay the full output verbatim to the user before asking for a response — do not summarize on their behalf.

---

## Step 5 — Apply changes

**Precondition:** User has confirmed which rewrites to apply.

Apply each approved rewrite to `TARGET` using targeted edits — replace only the specific text identified in `[CURRENT TEXT]`, leaving the rest of the file unchanged.

After all edits are complete, report how many changes were applied and which steps were modified.
