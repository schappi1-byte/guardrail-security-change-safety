# Guardrail Security Change Safety Agent - Working System

## What Was Built

A complete, production-ready Python agent that analyzes security changes (IAM policies) before deployment to identify what could break in production.

### Core Components

```
guardrail/
├── models/types.py              → 10 type-safe data classes
├── adapters/terraform_parser.py → Parses IAM policy diffs  
├── engines/dependency_engine.py → Maps roles → services → usage
├── engines/impact_engine.py     → Assesses impact & recommends steps
├── agent.py                     → Main orchestration
└── cli.py                       → Command-line interface
```

### How It Works

1. **Input**: Terraform diff with IAM policy changes
2. **Parse**: Extract the exact permissions being added/removed
3. **Trace**: Map from role → service account → workload → usage
4. **Assess**: Determine impact level (LOW/MEDIUM/HIGH/CRITICAL)
5. **Recommend**: Suggest safer rollout plan
6. **Output**: GitHub PR comment or JSON report

## Demo Scenario

**The Change**:
```terraform
- Actions = ["s3:GetObject"]
+ Actions = []
```

Removes `s3:GetObject` from `prod-app-reader` role.

**What Guardrail Finds**:
- 3 services depend on this role
- billing-api (PRODUCTION) — used s3:GetObject 143 times in 7 days
- invoice-worker (PRODUCTION) — used s3:GetObject 87 times in 7 days  
- reporting-job (STAGING) — used s3:GetObject 12 times in 7 days

**Recommendation**:
1. Create dedicated `billing-export-reader` role
2. Migrate billing-api and invoice-worker to new role
3. Verify 24 hours of successful access
4. Then remove permission from prod-app-reader

**Output**: HIGH IMPACT - Do NOT deploy without migration

## Key Capabilities

✅ **Evidence-Based** — Uses CloudTrail, not speculation
✅ **Production-Aware** — Distinguishes prod vs. staging
✅ **Confidence Levels** — HIGH/MEDIUM/LOW based on evidence
✅ **Safe Rollout Plans** — Step-by-step migration guides
✅ **GitHub Ready** — PR comments with findings
✅ **Dependency Tracing** — Role → SA → Workload → Usage
✅ **Impact Assessment** — CRITICAL/HIGH/MEDIUM/LOW levels

## Sample Data Included

**terraform_change.diff** — Real Terraform IAM change
**demo_dependencies.json** — Service dependencies and usage patterns

Both realistic and complete for testing.

## Repository Status

- **GitHub**: https://github.com/schappi1-byte/guardrail-security-change-safety
- **All code pushed**: ✅
- **Tests included**: ✅  
- **Documentation**: ✅ README, SKILL.md, guides
- **License**: MIT (open source)

## Next: Submit to CyberAgents Exchange

**Your fork branch is ready at**:
```
https://github.com/schappi1-byte/cyberagents-exchange/tree/add/guardrail-security-change-safety
```

**To complete submission**:
1. Visit your fork: https://github.com/schappi1-byte/cyberagents-exchange
2. Click the green "Compare & pull request" button
3. Click "Create pull request"
4. Done! ✅

The Tenable Exchange team will review in 2-5 business days.

---

## Summary

| Aspect | Status |
|--------|--------|
| Code Quality | ✅ Production-ready |
| Documentation | ✅ Comprehensive |
| Demo Scenario | ✅ Working |
| Tests | ✅ Included |
| GitHub | ✅ Live & pushed |
| Exchange PR | ✅ Branch ready |

**Guardrail is complete, tested, and ready for the CyberAgents Exchange.**
