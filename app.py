"""Streamlit UI for Guardrail Security Change Safety Agent."""

import streamlit as st
import json
from pathlib import Path
from guardrail.agent import GuardrailAgent
from guardrail.models.types import ImpactLevel

# Page config
st.set_page_config(
    page_title="Guardrail - Security Change Safety",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .impact-critical { color: #d91e1e; font-weight: bold; }
    .impact-high { color: #ff6b00; font-weight: bold; }
    .impact-medium { color: #ffa500; font-weight: bold; }
    .impact-low { color: #28a745; font-weight: bold; }
    .safe-no { color: #d91e1e; font-weight: bold; }
    .safe-yes { color: #28a745; font-weight: bold; }
    .metric-card {
        background: #f0f2f6;
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🛡️ Guardrail")
st.markdown("**Security Change Impact Safety Agent** — Identify what breaks before deploying IAM changes")

# Sidebar
with st.sidebar:
    st.header("Quick Start")
    st.info("""
    **How it works:**
    1. Paste your Terraform diff
    2. Configure service dependencies
    3. Get impact analysis
    4. Follow safe rollout plan
    """)
    
    use_demo = st.checkbox("📋 Use Demo Scenario", value=True)

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Terraform Change")
    
    if use_demo:
        demo_diff_path = Path("data/samples/terraform_change.diff")
        if demo_diff_path.exists():
            with open(demo_diff_path) as f:
                terraform_diff = f.read()
            st.info("✓ Loaded demo Terraform change")
            with st.expander("View Diff"):
                st.code(terraform_diff, language="diff")
        else:
            terraform_diff = ""
            st.error("Demo file not found")
    else:
        terraform_diff = st.text_area(
            "Paste Terraform diff (or leave empty for demo)",
            height=300,
            placeholder="--- a/terraform/iam.tf\n+++ b/terraform/iam.tf\n...",
            label_visibility="collapsed"
        )

with col2:
    st.subheader("⚙️ Dependencies Config")
    
    if use_demo:
        demo_config_path = Path("data/samples/demo_dependencies.json")
        if demo_config_path.exists():
            with open(demo_config_path) as f:
                dependency_config = json.load(f)
            st.info("✓ Loaded demo dependencies")
            with st.expander("View Config"):
                st.json(dependency_config)
        else:
            dependency_config = {}
            st.error("Demo config not found")
    else:
        config_text = st.text_area(
            "Paste JSON dependencies config or leave empty for demo",
            height=300,
            placeholder='{"services": [...], "usage_evidence": {...}}',
            label_visibility="collapsed"
        )
        try:
            dependency_config = json.loads(config_text) if config_text.strip() else {}
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
            dependency_config = {}

# Analysis button
if st.button("🔍 Analyze Change", use_container_width=True, type="primary"):
    if not terraform_diff.strip():
        st.error("❌ Please provide a Terraform diff")
    elif not dependency_config:
        st.error("❌ Please provide dependency configuration")
    else:
        st.divider()
        
        # Run analysis
        with st.spinner("Analyzing security impact..."):
            try:
                agent = GuardrailAgent()
                report = agent.analyze_terraform_change(
                    change_id="web-analysis",
                    terraform_diff=terraform_diff,
                    dependency_config=dependency_config
                )
                
                # Display results
                st.success("✅ Analysis complete")
                
                # Summary section
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    impact_text = str(report.overall_impact).replace("ImpactLevel.", "")
                    st.metric("Overall Impact", impact_text)
                
                with col2:
                    safe_text = "✅ YES" if report.safe_to_deploy else "❌ NO"
                    st.metric("Safe to Deploy", safe_text)
                
                with col3:
                    st.metric("Confidence", str(report.confidence).replace("ConfidenceLevel.", ""))
                
                with col4:
                    st.metric("Services Affected", len(report.impacts))
                
                st.divider()
                
                # Main findings
                st.subheader("📊 Analysis Summary")
                st.info(report.recommendation_summary)
                
                if report.warnings:
                    st.warning("**Warnings:**\n" + "\n".join(f"- {w}" for w in report.warnings))
                
                # IAM Changes
                if report.iam_changes:
                    st.subheader("🔐 IAM Changes Detected")
                    for change in report.iam_changes:
                        with st.expander(f"Role: {change.role_name}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if change.permissions_removed:
                                    st.write("**Removed Permissions:**")
                                    for perm in change.permissions_removed:
                                        st.code(f"{perm.action} on {perm.resource}")
                            
                            with col2:
                                if change.permissions_added:
                                    st.write("**Added Permissions:**")
                                    for perm in change.permissions_added:
                                        st.code(f"{perm.action} on {perm.resource}")
                                else:
                                    st.info("No permissions added")
                
                # Impacts
                if report.impacts:
                    st.subheader("💥 Impact Analysis")
                    
                    for impact in report.impacts:
                        # Color-code by impact level
                        impact_color = {
                            ImpactLevel.CRITICAL: "🔴",
                            ImpactLevel.HIGH: "🟠",
                            ImpactLevel.MEDIUM: "🟡",
                            ImpactLevel.LOW: "🟢"
                        }.get(impact.impact_level, "⚪")
                        
                        with st.expander(f"{impact_color} {impact.service.name} ({impact.service.environment})"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("Impact Level", str(impact.impact_level).replace("ImpactLevel.", ""))
                                st.metric("Confidence", str(impact.confidence).replace("ConfidenceLevel.", ""))
                            
                            with col2:
                                st.write(f"**Reason:** {impact.reason}")
                            
                            st.divider()
                            
                            if impact.evidence:
                                st.write("**Usage Evidence:**")
                                for evidence in (impact.evidence if isinstance(impact.evidence, list) else [impact.evidence]):
                                    st.code(f"{evidence.action} on {evidence.resource}\n"
                                           f"Used {evidence.count} times\n"
                                           f"Last seen: {evidence.last_seen}")
                else:
                    st.success("✅ No impacts detected - safe to deploy")
                
                # Recommendations
                st.subheader("📋 Recommended Rollout Plan")
                if report.recommended_steps:
                    for step in report.recommended_steps:
                        with st.expander(f"**Step {step.order}:** {step.action.replace('_', ' ').title()}", 
                                        expanded=step.order == 1):
                            st.write(f"**Description:** {step.description}")
                            st.write(f"**Rationale:** {step.rationale}")
                            st.info(f"⏱️ Estimated time: {step.estimated_time}")
                
                st.divider()
                
                # Export option
                st.subheader("📤 Export Report")
                report_json = {
                    "change_id": report.change_id,
                    "overall_impact": str(report.overall_impact),
                    "safe_to_deploy": report.safe_to_deploy,
                    "confidence": str(report.confidence),
                    "summary": report.recommendation_summary,
                    "warnings": report.warnings,
                    "steps_count": len(report.recommended_steps)
                }
                st.download_button(
                    label="📥 Download Report (JSON)",
                    data=json.dumps(report_json, indent=2),
                    file_name="guardrail_report.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                st.exception(e)

# Footer
st.divider()
st.markdown("""
---
**Guardrail Security Change Safety Agent**  
Dependency-aware IAM change impact assessment powered by CloudTrail evidence.
""")
