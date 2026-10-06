"""Main Guardrail security change safety agent."""

import json
from typing import Optional
from guardrail.models.types import SecurityChangeImpactReport
from guardrail.adapters.terraform_parser import TerraformParser
from guardrail.engines.dependency_engine import DependencyGraph
from guardrail.engines.impact_engine import ImpactAssessmentEngine


class GuardrailAgent:
    """Main agent that orchestrates security change impact analysis."""
    
    def __init__(self):
        self.dependency_graph = DependencyGraph()
        self.parser = TerraformParser()
        self.impact_engine = ImpactAssessmentEngine()
    
    def analyze_terraform_change(
        self,
        change_id: str,
        terraform_diff: str,
        dependency_config: Optional[dict] = None
    ) -> SecurityChangeImpactReport:
        """
        Analyze a Terraform change for security impact.
        
        Args:
            change_id: Unique identifier for this change
            terraform_diff: The diff content showing the changes
            dependency_config: Optional config with service dependencies and usage data
            
        Returns:
            SecurityChangeImpactReport with findings and recommendations
        """
        
        # Parse the Terraform diff to extract IAM changes
        iam_changes = self.parser.parse_terraform_diff(terraform_diff)
        
        # Build Terraform summary
        terraform_summary = "\n".join([
            self.parser.summarize_change(change) for change in iam_changes
        ])
        
        # Load dependency graph if provided
        if dependency_config:
            self._load_dependencies(dependency_config)
        
        # Analyze impacts
        all_impacts = []
        for change in iam_changes:
            impacts = self.dependency_graph.find_impacted_services(change)
            all_impacts.extend(impacts)
        
        # Generate report
        report = self.impact_engine.generate_report(
            change_id=change_id,
            terraform_summary=terraform_summary,
            iam_changes=iam_changes,
            impacts=all_impacts
        )
        
        return report
    
    def _load_dependencies(self, config: dict) -> None:
        """Load service dependencies and usage data from config."""
        
        # Load service dependencies
        for service_config in config.get("services", []):
            from guardrail.models.types import ServiceDependency
            service = ServiceDependency(
                service_name=service_config.get("name"),
                namespace=service_config.get("namespace", "default"),
                environment=service_config.get("environment", "production"),
                role_arn=service_config.get("role_arn", ""),
                service_account=service_config.get("service_account", "")
            )
            
            for role in service_config.get("roles", []):
                self.dependency_graph.add_role_dependency(role, service)
        
        # Load usage evidence
        for service_name, usages in config.get("usage_evidence", {}).items():
            from guardrail.models.types import UsageEvidence, ConfidenceLevel
            
            for usage_data in usages:
                usage = UsageEvidence(
                    service_name=service_name,
                    action=usage_data.get("action"),
                    resource=usage_data.get("resource"),
                    count=usage_data.get("count", 0),
                    last_seen=usage_data.get("last_seen", ""),
                    date_range=usage_data.get("date_range", "last 7 days"),
                    confidence=ConfidenceLevel(usage_data.get("confidence", "high"))
                )
                self.dependency_graph.add_usage_evidence(service_name, usage)
    
    def format_pr_comment(self, report: SecurityChangeImpactReport) -> str:
        """Format the report as a GitHub PR comment."""
        
        impact_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
        
        emoji = impact_emoji.get(report.overall_impact.value, "⚪")
        
        comment = f"""## {emoji} Security Change Impact Analysis

**Change ID:** `{report.change_id}`

### Summary
{report.recommendation_summary}

### Impact Level
**{report.overall_impact.value.upper()}** (Confidence: {report.confidence.value})

### Terraform Changes
```
{report.terraform_change_summary}
```

### Affected Services
"""
        
        if report.impacts:
            for impact in report.impacts:
                comment += f"\n#### {impact.service.service_name}\n"
                comment += f"- **Environment:** {impact.service.environment}\n"
                comment += f"- **Impact:** {impact.impact_level.value}\n"
                comment += f"- **Reason:** {impact.reason}\n"
                
                if impact.evidence:
                    comment += f"- **Evidence:** {impact.evidence.action} on {impact.evidence.resource}\n"
                    comment += f"  - Used {impact.evidence.count} times ({impact.evidence.date_range})\n"
                    comment += f"  - Last seen: {impact.evidence.last_seen}\n"
        else:
            comment += "\n**No production impact detected.** This change appears safe to deploy.\n"
        
        # Add recommendations
        comment += "\n### Recommended Rollout Plan\n"
        for step in report.recommended_steps:
            comment += f"\n**Step {step.order}:** {step.action}\n"
            comment += f"- {step.description}\n"
            comment += f"- Rationale: {step.rationale}\n"
            comment += f"- Estimated time: {step.estimated_time}\n"
        
        # Add warnings
        if report.warnings:
            comment += "\n### ⚠️ Warnings\n"
            for warning in report.warnings:
                comment += f"- {warning}\n"
        
        comment += f"\n---\n**Analysis by Guardrail Security Change Safety Agent**\n"
        comment += f"_Safe to deploy: **{'YES' if report.safe_to_deploy else 'NO'}**_"
        
        return comment
