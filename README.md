# Guardrail: Security Change Safety Agent

**Know what your security changes will break before you deploy them.**

Guardrail is an AI security change safety agent that identifies the real-world impact of security changes before they reach production. It analyzes infrastructure dependencies, permissions, configurations, and observed usage to determine what a change could break, provides evidence for each affected workload or service, and recommends a safer way to implement the change.

## The Problem

Security engineers regularly deploy changes to IAM policies, security groups, and access controls. But it's hard to predict what those changes will actually break:

- Which services depend on a specific permission?
- Do those services actually use that permission or is it unused legacy access?
- Which services are production vs. staging?
- What's the safest way to migrate if there's impact?

Without this information, security teams either over-privilege (to avoid breakage) or accidentally break production deployments.

## The Solution

Guardrail analyzes security changes **before deployment** by:

1. **Parsing** Terraform/IAM diffs to extract the exact permissions being changed
2. **Tracing dependencies** from roles to service accounts to workloads to actual resource usage
3. **Gathering evidence** from CloudTrail, deployment metadata, and IAM relationships
4. **Assessing impact** by matching removed permissions against actual observed usage
5. **Recommending safer rollouts** with step-by-step migration plans when high impact is detected

### Example Workflow

You open a PR that removes `s3:GetObject` from a shared IAM role:

```terraform
- Actions = ["s3:GetObject"]
+ Actions = []
```

Guardrail automatically:

- Finds all services using this role (billing-api, invoice-worker, reporting-job)
- Checks CloudTrail and sees that billing-api and invoice-worker actively use this permission
- Identifies billing-api and invoice-worker as production workloads
- Flags this as **HIGH IMPACT** because production services will break
- Recommends: create a new dedicated role, migrate billing-api and invoice-worker to it, verify access for 24 hours, then remove the permission

**Output**: A PR comment with evidence, impact assessment, and a step-by-step safer migration plan.

## Key Features

- **Evidence-based impact assessment** — not guesses, but actual CloudTrail usage patterns
- **Production vs. staging awareness** — understands environment criticality
- **Confidence levels** — distinguishes between confirmed impact and potential risk
- **Safer rollout plans** — recommends specific steps instead of "test more"
- **Dependency tracing** — maps IAM roles to Kubernetes service accounts to workloads to real usage
- **GitHub PR integration** — works in your existing code review workflow

## Architecture

Guardrail consists of four main engines:

1. **TerraformParser** — Extracts IAM changes from diffs
2. **DependencyGraph** — Maps roles to services to usage patterns
3. **ImpactAssessmentEngine** — Evaluates impact and confidence
4. **GuardrailAgent** — Orchestrates the analysis and produces reports

```
Terraform Diff
      ↓
TerraformParser
      ↓
IAM Changes
      ↓
DependencyGraph (find affected services)
      ↓
Evidence Collector (CloudTrail, metadata)
      ↓
ImpactAssessmentEngine
      ↓
SecurityChangeImpactReport
      ↓
GitHub PR Comment / Alert
```

## Installation

### Option 1: Clone to your global skills directory

```bash
git clone https://github.com/schappi1-byte/guardrail-security-change-safety.git ~/.claude/skills/guardrail
```

### Option 2: Clone to a specific project

```bash
git clone https://github.com/schappi1-byte/guardrail-security-change-safety.git .claude/skills/guardrail
```

### Option 3: Use as a Python module

```bash
pip install -e .
```

## Prerequisites

- Python 3.8+
- [AWS SDK (boto3)](https://boto3.amazonaws.com/) for CloudTrail analysis
- GitHub CLI (`gh`) for PR integration (optional)
- Terraform or HCL parser for policy diffs

## Quick Start

### 1. Create a dependency configuration

Create `guardrail-config.json` with your service dependencies and usage patterns:

```json
{
  "services": [
    {
      "name": "billing-api",
      "environment": "production",
      "role_arn": "arn:aws:iam::123456789012:role/prod-app-reader",
      "roles": ["prod-app-reader"]
    }
  ],
  "usage_evidence": {
    "billing-api": [
      {
        "action": "s3:GetObject",
        "resource": "arn:aws:s3:::prod-billing-data/*",
        "count": 143,
        "last_seen": "2024-10-06T02:07:00Z",
        "confidence": "high"
      }
    ]
  }
}
```

### 2. Analyze a change

```python
from guardrail.agent import GuardrailAgent
import json

# Initialize the agent
agent = GuardrailAgent()

# Load your config
with open('guardrail-config.json') as f:
    config = json.load(f)

# Analyze a Terraform change
with open('terraform_change.diff') as f:
    diff = f.read()

report = agent.analyze_terraform_change(
    change_id="pr-1234",
    terraform_diff=diff,
    dependency_config=config
)

# Format as a GitHub PR comment
pr_comment = agent.format_pr_comment(report)
print(pr_comment)
```

### 3. Example Output

```
🔴 Security Change Impact Analysis

Change ID: `pr-1234`

### Summary
This change will break 2 production service(s). Recommend creating new roles and migrating services before applying this change.

### Impact Level
HIGH (Confidence: high)

### Terraform Changes
Role: prod-app-reader
  Removed: 1 permission(s)
    - s3:GetObject on arn:aws:s3:::prod-billing-data/*

### Affected Services

#### billing-api
- **Environment:** production
- **Impact:** critical
- **Reason:** billing-api actively uses s3:GetObject on arn:aws:s3:::prod-billing-data/*
- **Evidence:** s3:GetObject on arn:aws:s3:::prod-billing-data/*
  - Used 143 times (last 7 days)
  - Last seen: 2024-10-06T02:07:00Z

#### invoice-worker
- **Environment:** production
- **Impact:** high
- **Reason:** invoice-worker assumes role prod-app-reader which is losing s3:GetObject
- **Evidence:** s3:GetObject on arn:aws:s3:::prod-billing-data/*
  - Used 87 times (last 7 days)
  - Last seen: 2024-10-05T15:30:00Z

### Recommended Rollout Plan

**Step 1:** create_new_role
- Create a new IAM role for the 2 affected production service(s)
- Rationale: Separate concerns and allow safe migration
- Estimated time: 10 minutes

**Step 2:** migrate_services
- Migrate affected services to the new role
- Rationale: Move workloads off the role being modified
- Estimated time: 1 hour

**Step 3:** verify_access
- Verify 24 hours of successful access from new role
- Rationale: Ensure migration is complete and stable
- Estimated time: 24 hours

**Step 4:** apply_change
- Apply the original IAM change
- Rationale: Now safe since dependent services have migrated
- Estimated time: 5 minutes

### ⚠️ Warnings
- CRITICAL: 1 production service(s) will be impacted. Do not deploy without migration plan.
- HIGH: 1 service(s) with frequent usage will be affected.

---
**Analysis by Guardrail Security Change Safety Agent**
_Safe to deploy: **NO**_
```

## Project Structure

```
guardrail/
├── __init__.py
├── agent.py                    # Main orchestration agent
├── models/
│   ├── __init__.py
│   └── types.py               # Data models and types
├── engines/
│   ├── __init__.py
│   ├── dependency_engine.py   # Role → service → usage mapping
│   └── impact_engine.py       # Impact assessment and recommendations
└── adapters/
    ├── __init__.py
    └── terraform_parser.py    # Terraform diff parsing

data/
├── samples/
│   ├── demo_dependencies.json # Example dependency config
│   └── terraform_change.diff  # Example Terraform change

tests/
├── test_agent.py
├── test_parser.py
├── test_dependency_engine.py
└── test_impact_engine.py

README.md
LICENSE
SKILL.md                       # Claude Code Skill definition
```

## Supported Input Types

- **Terraform** — HCL IAM policy changes
- **AWS IAM** — Direct policy diffs
- **GitHub** — PR-triggered analysis
- **Custom** — JSON dependency configs

## Integration Points

### GitHub Actions

Use Guardrail in your CI/CD pipeline:

```yaml
name: Security Change Analysis
on: [pull_request]

jobs:
  guardrail:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Guardrail analysis
        run: python -m guardrail.agent --pr-diff ${{ github.event.pull_request.diff_url }}
```

### AWS Integration

Connect to CloudTrail for actual usage evidence:

```python
import boto3
from guardrail.agent import GuardrailAgent

# Guardrail can query CloudTrail directly
cloudtrail = boto3.client('cloudtrail')
# ... build dependency config from CloudTrail data
```

### Slack Notifications

Post findings to Slack:

```python
slack_client.chat_postMessage(
    channel="#security-alerts",
    text=agent.format_pr_comment(report)
)
```

## Confidence Levels

Guardrail provides three confidence levels for impact assessment:

- **🟢 HIGH** — Direct CloudTrail evidence of usage
- **🟡 MEDIUM** — Inferred from role relationships but no direct usage evidence
- **🔴 LOW** — Only based on IAM structure, no usage patterns

Each impact claim includes the confidence level and the evidence behind it.

## Roadmap

- [ ] CloudTrail auto-integration (fetch usage patterns directly)
- [ ] Cost impact analysis (estimate remediation effort and downtime)
- [ ] Multi-cloud support (Azure, GCP)
- [ ] Kubernetes RBAC analysis
- [ ] Automated safe rollout orchestration
- [ ] Slack/Teams/email notifications
- [ ] Historical impact correlation (predict recurrence)

## Contributing

We welcome contributions! Areas we're looking for help:

- CloudTrail integration
- Azure/GCP support
- Kubernetes RBAC
- Better diff parsing
- Integration tests
- Documentation

## License

MIT License — see LICENSE file

## Security

If you discover a security issue, please email security@guardrail.dev instead of using the issue tracker.

## Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/schappi1-byte/guardrail-security-change-safety/issues)
- **Discussions**: [GitHub Discussions](https://github.com/schappi1-byte/guardrail-security-change-safety/discussions)

## About

Guardrail is built for the [Tenable CyberAgents Exchange](https://exchange.tenable.com/), a community directory for cybersecurity AI agents, skills, tools, and playbooks.

---

**Know what your security changes will break before you deploy them.**
