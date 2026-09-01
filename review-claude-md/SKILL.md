---
name: review-claude-md
description: "Review recent changes and suggest CLAUDE.md updates. Use when: CLAUDE.md feels stale, after a sprint of new patterns, after adding commands or tools, preparing for a new project phase. Optionally pass a focus area (e.g., 'testing patterns', 'new commands')."
argument-hint: "[focus-area]"
---

**STRICTLY READ-ONLY**: Do **not** modify `CLAUDE.md` or any other files. Output suggestions only. The user decides what to apply.

If a focus area was passed as an argument, restrict analysis to that area (e.g., "testing patterns", "new commands"). Otherwise, perform a full review.

## Instructions

1. Read the current `CLAUDE.md`. If it does not exist, abort and instruct the user to create one (e.g., run `/init`).

2. Gather changes since CLAUDE.md was last updated:
   - Run `git log -1 --format=%H -- CLAUDE.md` to find the last commit that touched CLAUDE.md
   - Use that SHA as the base: `git diff <sha>..HEAD --stat` and `git diff <sha>..HEAD`

   If no meaningful changes are found, report "No changes since last CLAUDE.md update" and stop.

3. Analyze the diff for patterns that warrant CLAUDE.md updates. Look for:
   - **New make targets or CLI commands** added to `Makefile` or `cmd/`
   - **New external service clients** (new packages in `internal/` or `adapters/`)
   - **New `//go:generate` directives** that should be listed in Code Generation
   - **New environment variables** (check the project's env var prefix from existing CLAUDE.md or config files)
   - **Changes to the architecture** (new layers, new handler registration patterns)
   - **New testing patterns** or test helpers not covered by existing guidance
   - **New database migration conventions** that differ from documented patterns
   - **New critical guardrails** implied by validation logic, sign handling, or sync constraints
   - **Removed or renamed packages/commands** that CLAUDE.md still references
   - **Missing verification steps** in procedural patterns (endpoint checklists, migration
     workflows, etc.) that have no "run this to confirm it worked" step

4. **CRITICAL**: Apply two filters:

   **For suggested additions** — ask: "Would the absence of this cause Claude to make a
   mistake it couldn't recover from by reading the code?"
   - If YES → suggest adding it. If NO → skip it. When in doubt, skip.

   **For existing entries** — ask: "Is this something Claude can figure out by reading the
   code, or does it duplicate content elsewhere in the file?"
   - Things to flag for removal: file-by-file directory trees, lists of integrations
     discoverable from imports, standard language conventions, self-evident practices,
     information that changes frequently (branch names, recent-changes logs).
   - A lean CLAUDE.md is better than a bloated one.

5. Also check for **stale entries**: anything in CLAUDE.md that no longer matches the
   codebase (deleted files, renamed commands, outdated paths) or **bloated entries**:
   content that was accurate when written but is now discoverable from code (e.g., a tech
   stack list after the codebase has matured and stabilized).

6. Output a summary with three sections:

   ### Suggested Additions

   For each, show the exact text to add and which CLAUDE.md section it belongs in.

   ### Suggested Modifications

   For each, show the current text and proposed replacement.

   ### Stale Entries to Remove

   For each, show the current text and why it's stale or bloated.

   If a section has no suggestions, print "None."

## Behavior Rules

- **NEVER** edit files — this skill is analysis only
- If CLAUDE.md is missing, abort with instructions rather than creating one
- If no changes exist to analyze, say so and stop — do not fabricate suggestions
- If all findings fail the filter in step 4, report "No CLAUDE.md updates needed" — a clean result is a good result
- Prefer fewer, higher-impact suggestions over comprehensive coverage
