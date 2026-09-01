---
name: gha-workflow-review
description: Review GitHub Actions workflow files for common migration and correctness issues. Use when a repo just migrated from CircleCI to GHA, when a workflow file was added or modified, or when the user asks to audit/review workflow files. Catches: missing CI jobs, broken deploy gates, wrong secret names, permissions gaps, missing Helm steps, bad Go CI patterns, and Slack notification gaps.
---

# GHA Workflow Review

## Quick start

Inventory the workflow files, then work through the checklist below.

```
ls .github/workflows/
```

## Step 1 — Inventory

Read all files in `.github/workflows/`. For each, note the trigger(s), the jobs it defines, and whether it is a deploy, CI/test, or utility workflow.

## Step 2 — Checklist

Work through all seven categories. Read the relevant workflow files if you haven't already.

If a sibling file named `SKILL.<company>.md` exists in this skill's directory, apply its additional/overriding checks after the generic checklist below.

### 1. Missing CI workflow

- [ ] At least one workflow triggers on `pull_request`
- [ ] That workflow runs the repo's test suite (e.g., `make test`, `go test ./...`)
- [ ] If the service has integration tests, the CI workflow includes a database service container

### 2. Deployment gating

Without an `environment:` block somewhere in the prod deploy chain, GHA skips protection rules — no human sign-off.

- [ ] The deploy pipeline includes at least one job with `environment:` set before production ships
- [ ] Production `needs:` includes staging (directly or via a gate job) — it cannot depend only on build/lint
- [ ] No `trstringer/manual-approval` action (replace with native `environment:` protection)

### 3. Secret names

Check secret names against `REFERENCE.md`'s guidance (or a company rider, if one exists, for org-specific overrides).

Also flag:

- `method: chat.postMessage` — use incoming webhook instead (see REFERENCE.md)

### 4. Permissions

- [ ] `permissions:` block exists at the **workflow level** (not only at the job level)
- [ ] When calling a reusable workflow via `uses:`, permissions are at the workflow level
- [ ] OIDC-based deploys include `id-token: write`
- [ ] Caller permissions are a superset of what the callee's jobs declare
- [ ] `claude-review-on-ready` callers: see REFERENCE.md for required permission set

### 5. Helm deploy steps

- [ ] Every job running `helm upgrade` is preceded by `helm repo add <your-chart-repo> ...` and `helm dependency build`
- [ ] Uses `helm dependency build` (locked, reproducible) — not `helm dependency update`

### 6. Go CI patterns

- [ ] Uses `go mod download`, not `go get ./...` (the latter can modify `go.mod` in CI)
- [ ] If a step runs `go run ./cmd/<svc> migrate`, all env vars the service validates at startup are set to placeholders

### 7. Notification completeness

- [ ] Each deploy job has both success (`if: success()`) and failure (`if: failure()`) Slack notification steps
- [ ] Notification text is correct per environment — no copy-paste errors (e.g., "tour succeeded" in the staging notification)

## Step 3 — Report

```markdown
## GHA workflow review: <repo>

### Critical
- **[Cat 2] No `environment:` gate before production** — `deploy.yml:L82`
  Production deploys without any approval gate. Add `environment: name: production`
  to the `release-prod` job, or add a dedicated gate job with `environment:` set.

### Issues
- **[Cat 3] Wrong AWS secret names** — `deploy.yml:L54`
  `secrets.AWS_NONPROD_ACCESS_KEY_ID` → use the org's canonical name (see company rider if present)

### Clean
Category 1 (CI workflow): ✓  ·  Category 4 (Permissions): ✓
```

**Critical** = broken deploy gates, credentials that would prevent all deploys from running.  
**Issues** = other correctness problems (wrong names, missing steps, pattern violations).  
List clean categories at the bottom. If all categories pass, say so explicitly.
