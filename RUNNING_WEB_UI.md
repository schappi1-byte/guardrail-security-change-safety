# 🛡️ Running Guardrail Web UI

## Quick Start

The Guardrail agent now has a beautiful, interactive web interface!

### Option 1: Flask Web UI (Recommended)

```bash
cd /tmp/guardrail-security-change-safety
python3 web_ui.py
```

Then open your browser to: **http://localhost:5000**

### Option 2: CLI Demo

```bash
python3 guardrail/cli.py demo
```

## Web UI Features

### 🎯 Simple Interface
- **Two-panel layout**: Terraform diff on the left, dependencies on the right
- **Demo mode**: Click checkbox to auto-load example data
- **Custom analysis**: Uncheck demo to paste your own data

### 📊 Visual Results
- **Impact metrics**: Overall impact level, safe to deploy flag, confidence, service count
- **Color-coded impacts**: 🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW
- **Service details**: Impact reason and usage evidence for each service
- **Rollout plan**: Step-by-step migration strategy with estimated time

### ⚙️ Built-In Demo Scenario

By default, loads:
- **Change**: Removing S3:GetObject permission from prod_app_reader role
- **Services Affected**:
  - billing-api (production) - CRITICAL impact
  - invoice-worker (production) - HIGH impact
  - reporting-job (staging) - MEDIUM impact
- **Result**: 🛑 Not safe to deploy - requires role migration first

Just click **🔍 Analyze Change** to see it in action!

## Workflow

1. **Paste Terraform Diff** (left panel)
   - Paste full Terraform diff with IAM changes
   - Or use demo scenario (default)

2. **Configure Dependencies** (right panel)
   - Provide JSON with services and their role dependencies
   - Include CloudTrail usage evidence for accuracy
   - Or use demo scenario (default)

3. **Click Analyze**
   - Agent parses the diff
   - Traces role dependencies to services
   - Matches against usage patterns
   - Generates impact assessment

4. **Review Results**
   - See affected services with impact levels
   - Get clear safe/not-safe recommendation
   - Follow recommended rollout plan

## Demo Dependencies JSON Format

```json
{
  "services": [
    {
      "name": "billing-api",
      "namespace": "prod",
      "environment": "production",
      "role_arn": "arn:aws:iam::123456789012:role/prod_app_reader",
      "roles": ["prod_app_reader"],
      "service_account": "billing-api-sa"
    }
  ],
  "usage_evidence": {
    "billing-api": [
      {
        "action": "s3:GetObject",
        "resource": "arn:aws:s3:::prod-billing-data/*",
        "count": 143,
        "last_seen": "2024-10-06T02:07:00Z",
        "date_range": "last 7 days",
        "confidence": "high"
      }
    ]
  }
}
```

## Example Terraform Diff

```diff
--- a/terraform/iam.tf
+++ b/terraform/iam.tf
@@ -15,7 +15,7 @@
 resource "aws_iam_role_policy" "prod_app_reader" {
   name   = "prod-app-reader-policy"
   role   = aws_iam_role.prod_app_reader.id
   policy = jsonencode({
     Version = "2012-10-17"
     Statement = [
       {
         Effect = "Allow"
-        Actions = ["s3:GetObject"]
+        Actions = []
         Resource = ["arn:aws:s3:::prod-billing-data/*"]
       }
     ]
   })
 }
```

## Troubleshooting

**Port 5000 already in use?**
```bash
# Find process using port 5000
lsof -i :5000

# Kill it
kill -9 <PID>

# Or use different port
python3 web_ui.py --port 8000
```

**Import errors?**
```bash
# Ensure dependencies are installed
pip install flask boto3

# Reinstall package in development mode
pip install -e .
```

**Demo data not loading?**
- Verify data files exist:
  - `data/samples/terraform_change.diff`
  - `data/samples/demo_dependencies.json`
- Check file permissions: `chmod 644 data/samples/*`

## Browser Compatibility

Works on all modern browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (responsive design)

## Architecture

```
┌─────────────────────────────────┐
│     Web Browser (HTML/JS)       │
│   - Terraform diff input        │
│   - Dependencies config input   │
│   - Results visualization       │
└────────────┬────────────────────┘
             │ HTTP JSON
┌────────────▼────────────────────┐
│      Flask Web Server           │
│  - /api/demo-data               │
│  - /api/analyze (POST)          │
└────────────┬────────────────────┘
             │ Python
┌────────────▼────────────────────┐
│   GuardrailAgent (Python)       │
│  - Parser (Terraform diffs)     │
│  - Dependency Graph             │
│  - Impact Assessment Engine     │
└─────────────────────────────────┘
```

## Next Steps

After analyzing a change:

1. **Review the rollout plan** - Follow recommended steps
2. **Test in staging first** - Verify access patterns
3. **Monitor CloudTrail** - Verify service usage patterns
4. **Gradual rollout** - Apply changes to canary services first
5. **Automate** - Integrate with CI/CD pipeline

---

**Questions?** Check README.md for more details on the Guardrail agent.
