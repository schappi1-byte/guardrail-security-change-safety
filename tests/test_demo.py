"""Tests for the Guardrail agent."""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from guardrail.agent import GuardrailAgent
from guardrail.models.types import ImpactLevel


def test_demo_scenario():
    """Test the demo scenario with sample Terraform change."""
    
    # Load sample data
    data_dir = Path(__file__).parent.parent / "data" / "samples"
    
    with open(data_dir / "demo_dependencies.json") as f:
        config = json.load(f)
    
    with open(data_dir / "terraform_change.diff") as f:
        terraform_diff = f.read()
    
    # Initialize agent
    agent = GuardrailAgent()
    
    # Analyze the change
    report = agent.analyze_terraform_change(
        change_id="demo-pr-1234",
        terraform_diff=terraform_diff,
        dependency_config=config
    )
    
    # Assertions
    assert report is not None
    assert report.change_id == "demo-pr-1234"
    assert len(report.iam_changes) > 0, "Should detect IAM changes"
    assert report.overall_impact in [
        ImpactLevel.HIGH, ImpactLevel.CRITICAL, ImpactLevel.MEDIUM, ImpactLevel.LOW
    ], "Impact level should be set"
    assert not report.safe_to_deploy, "Demo change should not be safe (removes permission)"
    assert len(report.recommended_steps) > 0, "Should recommend steps"
    
    print("✓ Demo scenario test passed")
    
    # Test PR comment generation
    pr_comment = agent.format_pr_comment(report)
    assert pr_comment is not None
    assert "Guardrail" in pr_comment or "security" in pr_comment.lower()
    assert "billing-api" in pr_comment or "impact" in pr_comment.lower()
    
    print("✓ PR comment generation test passed")
    
    # Print the report
    print("\n" + "="*60)
    print("GUARDRAIL DEMO ANALYSIS")
    print("="*60)
    print(pr_comment)
    print("="*60 + "\n")
    
    return report


if __name__ == "__main__":
    print("Running Guardrail demo tests...\n")
    report = test_demo_scenario()
    print("\n✓ All tests passed!")
