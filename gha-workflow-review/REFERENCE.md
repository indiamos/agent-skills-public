# GHA Workflow Review — Reference

## Canonical secret names

Check your org's canonical secret names (see a company rider, if one exists, for exact names). Common drift patterns to grepping for include bare `AWS_*_ACCESS_KEY_ID` without an org prefix, legacy Slack bot token names, and outdated GitHub packages token names.

## Slack notification pattern

Use incoming webhook (not the Slack Bot API). The webhook URL encodes the channel — no separate channel ID needed.

```yaml
- name: Notify Slack (success)
  if: success()
  uses: slackapi/slack-github-action@v1
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK_URL_POD_DEPLOYS }}
    webhook-type: incoming-webhook
    payload: |
      {"text": "✅ <service> <env> deploy succeeded"}

- name: Notify Slack (failure)
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK_URL_POD_DEPLOYS }}
    webhook-type: incoming-webhook
    payload: |
      {"text": "❌ <service> <env> deploy failed"}
```

## claude-review-on-ready: required permissions

The calling workflow must grant all of these at the **workflow level** (not the job level):

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
  id-token: write
  actions: read
```

Placing this block at the job level instead of the workflow level causes `startup_failure` when
the reusable callee workflow tries to claim those permissions.

## Deploy DAG — gate before production

Two valid patterns for requiring human approval before production ships:

**Pattern A — dedicated gate job:**

```yaml
post_staging_approval:
  needs: deploy_staging
  runs-on: ubuntu-latest
  permissions:
    contents: read
  environment: post-staging-approval
  steps:
    - run: echo "approved"

deploy_tour:
  needs: [build_image, post_staging_approval]
  ...

deploy_production:
  needs: [build_image, post_staging_approval]
  ...
```

**Pattern B — per-job environment gate:**

```yaml
release-staging:
  environment:
    name: staging
  ...

release-tour:
  environment:
    name: tour
  needs: [notify-prod-ready]  # must include all non-prod deploys, not just build

release-prod:
  environment:
    name: production
  needs: [notify-prod-ready]  # same — not just [helm-lint, build-and-push-image]
```

**Anti-pattern to flag (no gate):**

```yaml
release-prod:
  needs: [helm-lint, build-and-push-image]  # ❌ skips staging entirely
  # no environment: block                    # ❌ no protection rules
```

## Helm dependency commands

```yaml
- name: Add Helm repo
  run: |
    helm repo add <chart-repo> \
      --username x-access-token \
      --password ${{ secrets.GH_PACKAGES }} \
      https://raw.githubusercontent.com/<org>/<helm-repo>/gh-pages/

- name: Build Helm dependencies
  run: helm dependency build ./helm/<chart-name>
```

Use `helm dependency build` (reads Chart.lock — reproducible, no version changes) not
`helm dependency update` (re-resolves — can silently bump chart versions).

## Go: services with eager config validation

Some Go services validate all required config fields in `main()` before routing subcommands.
Running `go run ./cmd/<svc> migrate` in CI fails at startup unless all env vars are set.
Supply harmless placeholders in the CI step:

```yaml
- name: Run migrations
  env:
    SERVICE_CLOCKWORK_HOST: "localhost:443"
    SERVICE_AUTHZ_HOST: "localhost:443"
    SERVICE_BILLING_HOST: "localhost:443"
  run: go run ./cmd/<svc> migrate
```

Apply the same placeholders to integration test steps that invoke the service binary.
