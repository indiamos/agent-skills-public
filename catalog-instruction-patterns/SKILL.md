---
name: catalog-instruction-patterns
description: Use when you want to extract a reusable catalog of instruction patterns from a set of skill or command files — to inform writing new skills, auditing existing ones, or building a style guide for skill authors. Accepts any list of files or directories.
---

# Catalog Instruction Patterns

## Overview

Analyze a set of skill or command files, decompose them into atomic instruction nodes, classify each node by pattern type, and produce a catalog that a skill author can use to answer: "I want my skill to do X — which pattern applies, and what should the instruction look like?"

## Step 0 — Bind inputs before any other action

Read the arguments provided when the skill was invoked.

- **sources** — one or more file paths or directories to analyze

**STOP gate:** If no sources were provided, ask: "Which skill or command files should I analyze? Please provide one or more file paths or directories." Wait for a response before continuing.

For directories, include all `.md` files found directly in that directory (non-recursive unless the user specifies otherwise).

Carry `SOURCES` (the resolved list of file paths) through all remaining steps.

---

## Step 1 — Decompose each file into nodes

**Precondition:** `SOURCES` is bound and all files are readable.

A **node** is an instruction with exactly one trigger and exactly one outcome. Outcome types:

- `PRODUCES` — creates a variable, artifact, or file
- `HALTS` — stops execution with a message
- `BRANCHES` — routes to different subsequent actions based on a value
- `PAUSES` — waits for user input before continuing
- `DISPATCHES` — launches one or more subagents

Numbered steps in skill files often contain multiple nodes. Split them.

✅ CORRECT decomposition of a "bind reviewer identity" node:

```
[FILE] pr-scout/SKILL.md
[LOCATION] Step 0a
[TRIGGER] Step 0 begins
[OUTCOME] PRODUCES REVIEWER, or HALTS if the gh api call fails
[PATTERN] Command binding
[TEXT] Run: gh api user --jq '.login'
       Store the result as REVIEWER. If this fails, report the error and halt.
```

❌ WRONG decomposition:

```
[FILE] pr-scout/SKILL.md
[LOCATION] Step 0
[TRIGGER] Skill invoked
[OUTCOME] PRODUCES all state variables
[PATTERN] Input binding
[TEXT] Bind REVIEWER, PR_REF, PR_AUTHOR, OUTPUT, and CHECK_COMMITS.
```

(Too coarse — Step 0 contains five independent nodes, each of which can halt independently.)

**STOP gate:** If any source file cannot be read, report which file failed and ask whether to continue with the remaining files or halt.

---

## Step 2 — Record each node

Use this exact format for every node:

```
[FILE] filename only (no path)
[LOCATION] Step N / sub-step label / section heading
[TRIGGER] What causes this node to execute (one clause)
[OUTCOME] PRODUCES / HALTS / BRANCHES / PAUSES / DISPATCHES + brief description
[PATTERN] Name from the seed list (or a new name if nothing fits — see below)
[TEXT] The instruction verbatim, or — if over 60 words — a neutral paraphrase
       that preserves the structure but replaces domain-specific names with
       generic placeholders (e.g., OWNER/REPO, TARGET_FILE, ARTIFACT)
```

**Seed pattern names:**

| Name                    | What it does                                                                                                                                                                                                                                                                                                                                                         | Executable?              |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| Argument binding        | Read a value from user-provided arguments; pause to ask if absent                                                                                                                                                                                                                                                                                                    | Yes — PAUSES or PRODUCES |
| Command binding         | Run a tool call and store the result; halt if the call fails                                                                                                                                                                                                                                                                                                         | Yes — PRODUCES or HALTS  |
| Precondition annotation | Document what must be true at this point — structural convention, not enforcement                                                                                                                                                                                                                                                                                    | No (meta)                |
| STOP gate               | "If condition, halt with message" — binary: halt or proceed normally; continuing is the default path                                                                                                                                                                                                                                                                 | Yes — HALTS              |
| Conditional routing     | Two or more meaningfully different paths based on a value; halt may be one branch among others                                                                                                                                                                                                                                                                       | Yes — BRANCHES           |
| Parallel dispatch       | Launch N agents simultaneously; collect all results. **Format matters**: a table or explicit `<use_parallel_tool_calls>` directive signals parallelism — an `a.`/`b.`/`c.` ordered list does not. Note whether agents are constrained to their specific task (no re-running prior-step commands) and whether they produce complete artifacts at identification time. | Yes — DISPATCHES         |
| Output format spec      | Exact output structure with ✅/❌ examples                                                                                                                                                                                                                                                                                                                           | Yes — PRODUCES           |
| Scoring rubric          | Labeled scale with explicit per-level criteria                                                                                                                                                                                                                                                                                                                       | Yes — PRODUCES           |
| Preview-then-confirm    | Show output; wait for user approval before writing or posting                                                                                                                                                                                                                                                                                                        | Yes — PAUSES             |
| Skip rule               | Explicit criteria for what to exclude from processing                                                                                                                                                                                                                                                                                                                | No (meta)                |
| Annotation tagging      | Label items with a status marker before presenting them                                                                                                                                                                                                                                                                                                              | Yes — PRODUCES           |
| File-conditional        | Execute only if a specific file or directory exists                                                                                                                                                                                                                                                                                                                  | Yes — BRANCHES           |

**Decision rule for guard patterns** — choose among Precondition annotation, STOP gate, and Conditional routing:

- Use _Precondition annotation_ to document assumed state at the top of a step (e.g., `**State check:** X is bound from step N`) — not enforced, just declared
- Use _STOP gate_ when one condition should abort and the normal case simply continues — binary halt-or-proceed
- Use _Conditional routing_ when different values produce different meaningful behaviors (not just halt vs. proceed)

**Decision rule for binding patterns** — choose between Argument binding and Command binding:

- Use _Argument binding_ when the value comes from what the user typed (skill arguments or a prior prompt response)
- Use _Command binding_ when the value must be obtained by running a tool (shell command, API call, file read)

Add a new pattern name only when no seed name fits. Do not reuse a seed name for a structurally different instruction just because the topic overlaps.

---

## Step 3 — Select canonical examples

**State check:** All nodes from all source files are recorded.

Group nodes by pattern name. For each pattern, select the one example that best satisfies all three criteria:

1. **Generic**: contains no project names, service names, domain entity names, or file paths specific to one codebase — or has had those replaced with placeholders in `[TEXT]`
2. **Complete**: the `[TEXT]` alone is sufficient for a skill author to understand the pattern without reading the surrounding file
3. **Minimal**: the shortest example that still satisfies 1 and 2

If no single example satisfies all three, select two: the most generic and the most complete.

---

## Step 4 — Produce the catalog

Output one section per pattern, in this format:

```
## Pattern: <name>

**What it's for:** One sentence.
**Outcome type(s):** list the outcome types seen across all instances

### Canonical example
[FILE] ...
[LOCATION] ...
[TEXT] ...

### All instances
| File | Location | Notes |
|------|----------|-------|
```

After all pattern sections, append:

```
## Summary

| Pattern | Instance count | Files it appears in |
|---|---|---|
```

Present the catalog in the chat. Do not write it to a file unless the user asks.
