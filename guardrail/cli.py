"""Command-line interface for Guardrail."""

import argparse
import json
import sys
from pathlib import Path
from guardrail.agent import GuardrailAgent


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Guardrail: Know what your security changes will break before you deploy them.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a Terraform change with dependency config
  guardrail analyze --terraform-diff change.diff --config guardrail-config.json
  
  # Run the demo scenario
  guardrail demo
  
  # Show version
  guardrail --version
        """
    )
    
    parser.add_argument("--version", action="store_true", help="Show version")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a security change")
    analyze_parser.add_argument(
        "--terraform-diff",
        required=True,
        help="Path to Terraform diff file"
    )
    analyze_parser.add_argument(
        "--config",
        required=True,
        help="Path to dependency configuration JSON"
    )
    analyze_parser.add_argument(
        "--change-id",
        default="change-1",
        help="Unique identifier for this change"
    )
    analyze_parser.add_argument(
        "--output-format",
        choices=["pr-comment", "json", "text"],
        default="pr-comment",
        help="Output format"
    )
    
    # demo subcommand
    demo_parser = subparsers.add_parser("demo", help="Run the demo scenario")
    
    args = parser.parse_args()
    
    if args.version:
        print("Guardrail 1.0.0")
        return 0
    
    if args.command == "analyze":
        return handle_analyze(args)
    elif args.command == "demo":
        return handle_demo()
    else:
        parser.print_help()
        return 0


def handle_analyze(args):
    """Handle the analyze command."""
    
    try:
        # Load Terraform diff
        diff_path = Path(args.terraform_diff)
        if not diff_path.exists():
            print(f"Error: Terraform diff file not found: {args.terraform_diff}", file=sys.stderr)
            return 1
        
        with open(diff_path) as f:
            terraform_diff = f.read()
        
        # Load dependency config
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Config file not found: {args.config}", file=sys.stderr)
            return 1
        
        with open(config_path) as f:
            config = json.load(f)
        
        # Initialize agent and analyze
        agent = GuardrailAgent()
        report = agent.analyze_terraform_change(
            change_id=args.change_id,
            terraform_diff=terraform_diff,
            dependency_config=config
        )
        
        # Output based on format
        if args.output_format == "pr-comment":
            print(agent.format_pr_comment(report))
        elif args.output_format == "json":
            # Convert report to JSON
            report_dict = {
                "change_id": report.change_id,
                "overall_impact": report.overall_impact.value,
                "confidence": report.confidence.value,
                "safe_to_deploy": report.safe_to_deploy,
                "impacts": len(report.impacts),
                "recommendations": len(report.recommended_steps),
                "warnings": report.warnings
            }
            print(json.dumps(report_dict, indent=2))
        else:  # text
            print(f"Change ID: {report.change_id}")
            print(f"Overall Impact: {report.overall_impact.value.upper()}")
            print(f"Confidence: {report.confidence.value}")
            print(f"Safe to Deploy: {report.safe_to_deploy}")
            print(f"Affected Services: {len(report.impacts)}")
            print(f"Recommended Steps: {len(report.recommended_steps)}")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_demo():
    """Run the demo scenario."""
    
    try:
        # Import here to avoid issues if test data not available
        import tests.test_demo
        
        print("\n" + "="*70)
        print("GUARDRAIL SECURITY CHANGE IMPACT ANALYSIS - DEMO")
        print("="*70 + "\n")
        
        report = tests.test_demo.test_demo_scenario()
        
        print("\n✓ Demo completed successfully!")
        return 0
    
    except Exception as e:
        print(f"Error running demo: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
