# AWS Cost Copilot Implementation Plan

## Goal

Build a working Slack app that lets a user ask AWS cost questions from Slack and receive useful cost summaries, alerts, and recommendations.

The current repo is mostly a deployable AWS CDK scaffold. The implementation work will turn it into a production-shaped MVP:

- Slack slash command endpoint
- Slack interactive endpoint
- Slack OAuth install callback
- Secure Slack signature verification
- Workspace installation storage
- AWS Cost Explorer integration
- DynamoDB persistence
- Scheduled cost checks and alerts
- Tests, deployment docs, and smoke checks

## MVP User Experience

The first working version should support these Slack commands:

```text
/cost today
/cost yesterday
/cost month
/cost last 7 days
/cost service
/cost service EC2
/cost help
```

Example responses:

```text
AWS cost for today so far: $12.43
Top services:
1. Amazon EC2 - $7.91
2. Amazon RDS - $2.12
3. AWS Lambda - $0.42
```

```text
AWS cost for this month: $348.22
Projected month-end cost: $612.40
Highest service: Amazon EC2 at $201.10
```

## Target Architecture

```text
Slack
  |
  | slash commands, interactivity, OAuth callback
  v
API Gateway HTTP API
  |
  +-- GET  /health
  +-- POST /slack/commands
  +-- POST /slack/interactivity
  +-- GET  /auth/slack/callback
  v
Node.js Lambda functions
  |
  +-- Slack signature verification
  +-- Slack OAuth token exchange
  +-- command parsing
  +-- AWS Cost Explorer calls
  +-- DynamoDB persistence
  +-- Slack response formatting
  v
DynamoDB
  |
  +-- workspace installs
  +-- user settings
  +-- command audit records
  +-- alert subscriptions
  +-- cached cost summaries

Secrets Manager
  |
  +-- Slack signing secret
  +-- Slack client ID
  +-- Slack client secret
  +-- Slack bot token fallback if needed

EventBridge Scheduler
  |
  v
scheduled-alert Lambda
  |
  +-- checks cost thresholds
  +-- sends Slack alerts
```

## Proposed Repo Structure

```text
aws-cost-copilot/
  README.md
  docs/
    IMPLEMENTATION_PLAN.md
    DEPLOYMENT.md
    SLACK_APP_SETUP.md
    OPERATIONS.md

  infra/
    app.py
    cdk.json
    requirements.txt
    stacks/
      app_stack.py
    stages/
      app_stage.py
    cdk_constructs/
      api.py
      dynamodb.py
      kms_ssm.py
      lambdas.py
      layer.py
      scheduler.py

  services/
    health/
      package.json
      src/index.js
    commands/
      package.json
      src/index.js
    interactivity/
      package.json
      src/index.js
    oauth_callback/
      package.json
      src/index.js
    scheduled_alerts/
      package.json
      src/index.js

  shared/
    package.json
    src/
      aws-cost-explorer.js
      dynamodb.js
      http.js
      logger.js
      slack-format.js
      slack-oauth.js
      slack-signature.js
      time.js
      validation.js

  layers/
    shared-node18/
      nodejs/
        package.json
        package-lock.json
        node_modules/
        lib/
          hello.js

  tests/
    smoke.sh
    postman_collection.json
    unit/
      command-parser.test.js
      slack-signature.test.js
      slack-format.test.js
```

## Data Model

Use a single DynamoDB table with `pk` and `sk`.

### Workspace Install

```text
pk: WORKSPACE#<slack_team_id>
sk: INSTALL
```

Attributes:

```json
{
  "teamId": "T123",
  "teamName": "Example Workspace",
  "enterpriseId": null,
  "botUserId": "U123",
  "botAccessTokenSecretRef": "/aws-cost-copilot/dev/slack/install/T123/bot_token",
  "installedBy": "U456",
  "installedAt": "2026-07-05T00:00:00.000Z"
}
```

### User Settings

```text
pk: WORKSPACE#<slack_team_id>
sk: USER#<slack_user_id>
```

Attributes:

```json
{
  "defaultRange": "month",
  "defaultGroupBy": "SERVICE"
}
```

### Alert Subscription

```text
pk: WORKSPACE#<slack_team_id>
sk: ALERT#<alert_id>
```

Attributes:

```json
{
  "channelId": "C123",
  "createdBy": "U123",
  "thresholdUsd": 500,
  "period": "month",
  "enabled": true,
  "lastTriggeredAt": null
}
```

### Command Audit

```text
pk: WORKSPACE#<slack_team_id>
sk: COMMAND#<timestamp>#<request_id>
```

Attributes:

```json
{
  "command": "/cost",
  "text": "month",
  "channelId": "C123",
  "userId": "U123",
  "responseStatus": "ok",
  "createdAt": "2026-07-05T00:00:00.000Z"
}
```

## Environment Variables

All Lambda functions:

```text
APP_NAME
ENV
TABLE_NAME
LOG_LEVEL
```

Slack handlers:

```text
SLACK_SIGNING_SECRET_ARN
SLACK_CLIENT_ID_SECRET_ARN
SLACK_CLIENT_SECRET_ARN
```

Optional:

```text
AWS_COST_REGION=us-east-1
COST_CACHE_TTL_SECONDS=900
```

## Secrets Manager

Create these secrets through CDK:

```text
/aws-cost-copilot/dev/slack/signing_secret
/aws-cost-copilot/dev/slack/client_id
/aws-cost-copilot/dev/slack/client_secret
```

For installed workspaces, create per-workspace bot token secrets:

```text
/aws-cost-copilot/dev/slack/install/<team_id>/bot_token
```

## Implementation Phases

### Phase 1: Clean Up Repo Shape

Tasks:

- Confirm the nested `aws-cost-copilot/` directory is the canonical repo.
- Move or remove unused top-level scaffold files only after confirming they are no longer needed.
- Decide whether to keep direct Lambda packaging or switch back to `NodejsFunction`.
- Keep direct Lambda packaging for MVP to avoid Docker/esbuild complexity.
- Update comments that still reference `infra/constructs` instead of `infra/cdk_constructs`.
- Fill in `README.md` with purpose, setup, deploy, and test instructions.

Acceptance criteria:

- `cdk synth` works from `infra/`.
- README explains local setup and deployment.
- No duplicate active Lambda construct paths.

### Phase 2: Shared Runtime Utilities

Create shared modules:

- `shared/src/http.js`
- `shared/src/logger.js`
- `shared/src/slack-signature.js`
- `shared/src/slack-format.js`
- `shared/src/slack-oauth.js`
- `shared/src/dynamodb.js`
- `shared/src/aws-cost-explorer.js`
- `shared/src/time.js`
- `shared/src/validation.js`

Responsibilities:

- consistent JSON/text HTTP responses
- structured logs
- Slack request verification
- Slack Block Kit formatting
- DynamoDB get/put/query helpers
- Cost Explorer queries
- date range parsing
- command input validation

Acceptance criteria:

- Shared utilities can be imported by all services.
- Unit tests cover signature verification and command/date parsing.

### Phase 3: Slack Signature Verification

Implement Slack verification for:

- `/slack/commands`
- `/slack/interactivity`

Required checks:

- `X-Slack-Request-Timestamp` exists
- timestamp is within 5 minutes
- `X-Slack-Signature` exists
- HMAC SHA256 matches `v0:<timestamp>:<raw_body>`

Acceptance criteria:

- invalid signatures return HTTP 401
- stale timestamps return HTTP 401
- valid signed requests continue to command parsing

### Phase 4: Slash Command Handler

Implement `services/commands/src/index.js`.

Responsibilities:

- verify Slack signature
- parse form-encoded Slack slash command body
- acknowledge within 3 seconds
- support command text:
  - `help`
  - `today`
  - `yesterday`
  - `month`
  - `last 7 days`
  - `service`
  - `service <name>`
- call AWS Cost Explorer
- format Slack response
- write command audit item to DynamoDB

Initial response strategy:

- For quick Cost Explorer queries, return response directly.
- If queries become slow, return an immediate ephemeral response and use `response_url` for async follow-up.

Acceptance criteria:

- `/cost help` returns help text.
- `/cost month` returns current month cost.
- `/cost service` returns top services for current month.
- command audit is persisted.

### Phase 5: AWS Cost Explorer Integration

Implement `shared/src/aws-cost-explorer.js`.

Supported functions:

- `getTotalCost({ startDate, endDate, granularity })`
- `getCostByService({ startDate, endDate, limit })`
- `getMonthForecast()`

Use AWS SDK v3:

```text
@aws-sdk/client-cost-explorer
```

Required IAM permissions:

```text
ce:GetCostAndUsage
ce:GetCostForecast
```

Acceptance criteria:

- Lambda role can call Cost Explorer.
- `/cost month` returns real AWS billing data.
- `/cost service` returns real service breakdown.

### Phase 6: Slack OAuth Install

Implement `services/oauth_callback/src/index.js`.

Responsibilities:

- accept Slack `code` query parameter
- exchange code with Slack OAuth API
- store workspace installation in DynamoDB
- store bot token in Secrets Manager
- return a simple success/failure HTML page

Required Slack scopes:

```text
commands
chat:write
chat:write.public
```

Optional future scopes:

```text
channels:read
groups:read
im:read
mpim:read
```

Acceptance criteria:

- installing the Slack app stores an install record.
- bot token is not stored directly in DynamoDB.
- callback returns useful success/error pages.

### Phase 7: Interactivity Handler

Implement `services/interactivity/src/index.js`.

Initial supported actions:

- refresh cost summary
- switch date range
- show top services
- dismiss message

Responsibilities:

- verify Slack signature
- parse interactive payload
- load workspace install
- run requested action
- return/update Slack message

Acceptance criteria:

- buttons from `/cost month` work.
- invalid action IDs return a safe error.

### Phase 8: Scheduled Alerts

Add a new service:

```text
services/scheduled_alerts/
```

Add a new construct:

```text
infra/cdk_constructs/scheduler.py
```

Responsibilities:

- EventBridge schedule invokes alert Lambda
- alert Lambda scans/query enabled alert subscriptions
- fetches current AWS cost
- posts to Slack if threshold is exceeded
- updates `lastTriggeredAt`

Initial command support:

```text
/cost alert month 500
/cost alerts
/cost alert delete <id>
```

Acceptance criteria:

- a user can create a monthly threshold alert.
- scheduled Lambda posts to Slack when threshold is exceeded.
- duplicate alert spam is avoided.

### Phase 9: Infrastructure Updates

Update CDK:

- add Slack client ID/client secret placeholders
- pass relevant secret ARNs to Lambdas
- grant Cost Explorer permissions to command and scheduled alert Lambdas
- grant Secrets Manager write permission to OAuth callback for per-workspace bot token secrets
- add scheduled alert Lambda
- add EventBridge schedule
- output API URL and key Slack URLs

Acceptance criteria:

- `cdk synth` succeeds.
- generated IAM policies are scoped to required actions.
- deployed API routes match Slack app configuration needs.

### Phase 10: Tests

Add unit tests for:

- Slack signature verification
- Slack command parsing
- date range parsing
- Slack response formatting
- Cost Explorer response normalization

Add integration/smoke tests:

- `/health`
- invalid Slack signature rejected
- `/cost help` with a valid test signature

Acceptance criteria:

- test command runs locally.
- smoke test can run against deployed API.

### Phase 11: Documentation

Create:

- `README.md`
- `docs/DEPLOYMENT.md`
- `docs/SLACK_APP_SETUP.md`
- `docs/OPERATIONS.md`

README should cover:

- what the app does
- architecture summary
- prerequisites
- local setup
- deploy
- configure Slack
- smoke test

Slack setup doc should cover:

- app creation
- slash command URL
- interactivity URL
- OAuth redirect URL
- scopes
- installing to workspace
- updating Secrets Manager values

Operations doc should cover:

- logs
- common failures
- rotating Slack secrets
- deleting dev stack
- cost considerations

Acceptance criteria:

- a new developer can deploy and install the Slack app using docs only.

## Detailed Build Order

1. Create this implementation plan.
2. Add README and setup docs.
3. Add shared utility modules.
4. Add package dependencies to Lambda services/layer.
5. Implement Slack signature verification.
6. Implement command parser.
7. Implement `/cost help`.
8. Implement Cost Explorer client.
9. Implement `/cost today`, `/cost yesterday`, `/cost month`.
10. Implement `/cost service`.
11. Add DynamoDB command audit writes.
12. Add IAM permissions for Cost Explorer.
13. Run `cdk synth`.
14. Deploy dev stack.
15. Configure Slack app routes.
16. Implement OAuth callback.
17. Store Slack install records.
18. Add interactivity buttons.
19. Add scheduled alerts.
20. Add unit and smoke tests.
21. Polish docs and error handling.

## Local Development Commands

From repo root:

```bash
cd infra
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk synth
```

Deploy:

```bash
cd infra
source ../scripts/env-dev.sh
cdk deploy
```

Smoke test:

```bash
API=https://your-api-id.execute-api.us-west-2.amazonaws.com/prod ./tests/smoke.sh
```

## AWS Permissions Needed By The App

Lambda runtime permissions:

```text
dynamodb:GetItem
dynamodb:PutItem
dynamodb:UpdateItem
dynamodb:Query
dynamodb:Scan
secretsmanager:GetSecretValue
secretsmanager:CreateSecret
secretsmanager:PutSecretValue
ce:GetCostAndUsage
ce:GetCostForecast
logs:CreateLogGroup
logs:CreateLogStream
logs:PutLogEvents
```

Deployment permissions:

The deployer needs normal CDK deployment permissions for:

- CloudFormation
- Lambda
- API Gateway v2
- DynamoDB
- IAM
- Secrets Manager
- EventBridge
- CloudWatch Logs

## Slack App Configuration

Use these URLs after deployment:

```text
Slash command:
https://<api-id>.execute-api.<region>.amazonaws.com/prod/slack/commands

Interactivity:
https://<api-id>.execute-api.<region>.amazonaws.com/prod/slack/interactivity

OAuth redirect:
https://<api-id>.execute-api.<region>.amazonaws.com/prod/auth/slack/callback
```

Slash command:

```text
/cost
```

OAuth scopes:

```text
commands
chat:write
chat:write.public
```

## Error Handling Rules

- Never expose raw secret values in logs or Slack responses.
- Return simple user-facing errors in Slack.
- Log structured technical details in CloudWatch.
- Slack signature failures should return 401 without extra detail.
- Cost Explorer failures should return a friendly Slack message and log the AWS error.
- OAuth failures should return a clear HTML error page.

## Security Rules

- Verify every Slack request except `/health` and OAuth callback.
- Store bot tokens in Secrets Manager, not DynamoDB.
- Keep DynamoDB records free of token values.
- Scope IAM permissions by table ARN and secret path where possible.
- Use timestamp tolerance for Slack signature verification.
- Avoid logging raw Slack request bodies after OAuth or token exchange.

## Production Hardening After MVP

- Add Slack Enterprise Grid support.
- Add account/team-level authorization.
- Add multi-account AWS support.
- Add AWS Organizations account breakdowns.
- Add budgets integration.
- Add anomaly detection.
- Add cached daily summaries.
- Add dashboards.
- Add CI/CD workflow.
- Add alarms for Lambda errors and API 5xx.
- Add CloudWatch dashboard.
- Add secret rotation process.

## Definition Of Done For Working App

The app is considered working when:

- CDK deploys successfully into dev.
- Slack app can be installed into a workspace.
- `/cost help` works in Slack.
- `/cost month` returns real AWS Cost Explorer data.
- `/cost service` returns top service costs.
- Invalid Slack signatures are rejected.
- Workspace install data is persisted.
- Bot token is stored in Secrets Manager.
- README and Slack setup docs are usable.
- Smoke tests pass against the deployed API.

