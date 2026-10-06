# Guardrail

**Know what your security changes will break before you deploy them.**

Guardrail is an AI security change safety agent that identifies the real-world impact of security changes before they reach production.

## What This Skill Does

When you ask Guardrail to analyze a security change, it:

1. **Parses** your Terraform or IAM policy changes
2. **Traces dependencies** from roles to workloads to actual resource usage
3. **Gathers evidence** from CloudTrail and deployment metadata
4. **Assesses impact** on production and staging services
5. **Recommends a safer rollout plan** if high impact is detected

### Example

You have a PR that removes an IAM permission:

```terraform
- Actions = ["s3:GetObject"]
+ Actions = []
```

Ask Guardrail: **"Analyze this security change for impact"**

Guardrail responds:

> 🔴 **HIGH IMPACT**
>
> This change will break `billing-api` in production.
>
> **Evidence:** CloudTrail shows billing-api used s3:GetObject 143 times in the last 7 days.
>
> **Recommended safer approach:**
> 1. Create a new dedicated billing-reader role
> 2. Migrate billing-api to it
> 3. Verify 24 hours of successful access
> 4. Then remove the permission from the shared role

## How to Use

### In Claude Code

1. **Ask directly:**
   ```
   Analyze this Terraform IAM change for security impact
   ```

2. **Provide the change:**
   - Paste your `terraform diff`
   - Or link to a GitHub PR
   - Or upload a Terraform file

3. **Get the analysis:**
   - Impact assessment (HIGH / MEDIUM / LOW)
   - List of affected services
   - Evidence from CloudTrail
   - Step-by-step safer rollout plan

### In a GitHub PR

Use `/guardrail analyze` in a PR comment to trigger analysis on the PR's changes.

### From the CLI

```bash
guardrail analyze --terraform-diff my-change.diff --config guardrail-config.json
```

## What You Need to Provide

Guardrail auto-detects as much as possible, but works best with:

- **Terraform changes** — the diff or file changes you're deploying
- **Dependency config** — which services depend on which IAM roles
- **Usage patterns** — how often services actually use each permission

A minimal config looks like:

```json
{
  "services": [
    {
      "name": "billing-api",
      "environment": "production",
      "roles": ["prod-app-reader"]
    }
  ],
  "usage_evidence": {
    "billing-api": [
      {
        "action": "s3:GetObject",
        "resource": "arn:aws:s3:::prod-billing-data/*",
        "count": 143,
        "confidence": "high"
      }
    ]
  }
}
```

## Framework & Integrations

- **Framework**: Python 3.8+, AWS SDK (boto3)
- **Integrations**: 
  - AWS IAM
  - Terraform
  - GitHub (PR comments)
  - CloudTrail (usage evidence)
  - Kubernetes (service accounts)

## Supported Platforms

- Claude Code
- Cursor
- Windsurf
- Any IDE supporting the Agent Skills standard

## Key Features

- ✅ Evidence-based impact assessment (not guesses)
- ✅ Production vs. staging awareness
- ✅ Confidence levels for each finding
- ✅ Step-by-step safer rollout plans
- ✅ GitHub PR integration
- ✅ CloudTrail usage evidence
- ✅ Dependency tracing

## Example Scenarios

### Scenario 1: Removing Unused Permission

```
Your change: Remove s3:GetObject from a shared role
Guardrail: "No CloudTrail evidence of usage. Safe to remove."
```

### Scenario 2: Breaking Production Workload

```
Your change: Remove s3:GetObject
Guardrail: "billing-api in production will break. Used 143 times last 7 days. 
           Recommend migrating to dedicated role first."
```

### Scenario 3: Mixed Impact

```
Your change: Restrict access to specific S3 bucket
Guardrail: "Production impact: high. Staging impact: low.
           Recommend testing in staging first, then migrate production services."
```

## How It Works

Guardrail uses a dependency-aware approach:

```
IAM Role
   ↓
Service Account (Kubernetes)
   ↓
Workload / Service
   ↓
Actual Resource Usage (CloudTrail)
```

When you change a permission, Guardrail traces backward through this chain to find:
- Which services depend on it
- Whether they actually use it
- Whether they're production or staging
- Whether the change will break them

Then it recommends a safer way to make the change.

## Getting Started

### Minimal Example

1. Paste a Terraform change
2. Provide a list of services that use the IAM role
3. Guardrail analyzes and recommends

### Full Example with Evidence

1. Terraform change
2. Service dependencies (Kubernetes deployment names)
3. CloudTrail usage patterns
4. Guardrail produces detailed impact report with evidence

## Questions?

- Check the [GitHub repository](https://github.com/schappi1-byte/guardrail-security-change-safety)
- See the [documentation](README.md)
- Open an [issue](https://github.com/schappi1-byte/guardrail-security-change-safety/issues)

---

**Guardrail: Know what your security changes will break before you deploy them.**
