"""Impact assessment and recommendation engine."""

from typing import List
from guardrail.models.types import (
    SecurityChangeImpactReport, IAMChange, Impact, 
    ImpactLevel, ConfidenceLevel, RecommendedStep
)


class ImpactAssessmentEngine:
    """Analyzes impacts and generates recommendations."""
    
    @staticmethod
    def generate_report(
        change_id: str,
        terraform_summary: str,
        iam_changes: List[IAMChange],
        impacts: List[Impact]
    ) -> SecurityChangeImpactReport:
        """Generate a complete impact assessment report."""
        
        # Calculate overall impact
        overall_impact = ImpactAssessmentEngine._calculate_overall_impact(impacts)
        confidence = ImpactAssessmentEngine._calculate_confidence(impacts)
        
        # Determine if safe to deploy
        safe_to_deploy = overall_impact not in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]
        
        # Generate recommendations
        recommendations = ImpactAssessmentEngine._generate_recommendations(
            iam_changes, impacts, safe_to_deploy
        )
        
        # Build warnings
        warnings = ImpactAssessmentEngine._build_warnings(impacts)
        
        # Build recommendation summary
        summary = ImpactAssessmentEngine._build_summary(impacts, overall_impact)
        
        return SecurityChangeImpactReport(
            change_id=change_id,
            terraform_change_summary=terraform_summary,
            iam_changes=iam_changes,
            impacts=impacts,
            overall_impact=overall_impact,
            confidence=confidence,
            recommendation_summary=summary,
            recommended_steps=recommendations,
            safe_to_deploy=safe_to_deploy,
            warnings=warnings
        )
    
    @staticmethod
    def _calculate_overall_impact(impacts: List[Impact]) -> ImpactLevel:
        """Determine the highest impact level."""
        if not impacts:
            return ImpactLevel.LOW
        
        impact_levels = [ImpactLevel.CRITICAL, ImpactLevel.HIGH, ImpactLevel.MEDIUM, ImpactLevel.LOW]
        
        for level in impact_levels:
            if any(impact.impact_level == level for impact in impacts):
                return level
        
        return ImpactLevel.LOW
    
    @staticmethod
    def _calculate_confidence(impacts: List[Impact]) -> ConfidenceLevel:
        """Calculate average confidence in the assessment."""
        if not impacts:
            return ConfidenceLevel.LOW
        
        # Check how many impacts have evidence
        with_evidence = sum(1 for i in impacts if i.evidence is not None)
        
        if with_evidence == len(impacts):
            return ConfidenceLevel.HIGH
        elif with_evidence >= len(impacts) * 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    @staticmethod
    def _generate_recommendations(
        iam_changes: List[IAMChange],
        impacts: List[Impact],
        safe_to_deploy: bool
    ) -> List[RecommendedStep]:
        """Generate recommended rollout steps."""
        steps = []
        
        if safe_to_deploy:
            steps.append(RecommendedStep(
                order=1,
                action="validate_change",
                description="Review the Terraform change in isolation",
                rationale="Ensure the change matches your security intent",
                estimated_time="5 minutes"
            ))
            
            steps.append(RecommendedStep(
                order=2,
                action="test_in_staging",
                description="Deploy this change to staging environment first",
                rationale="Verify behavior before production deployment",
                estimated_time="30 minutes"
            ))
            
            steps.append(RecommendedStep(
                order=3,
                action="deploy_to_production",
                description="Deploy to production during low-impact window",
                rationale="Minimize any potential disruption",
                estimated_time="15 minutes"
            ))
        else:
            # High impact - suggest safer migration
            production_impacts = [i for i in impacts if i.service.environment == "production"]
            
            if production_impacts:
                steps.append(RecommendedStep(
                    order=1,
                    action="create_new_role",
                    description=f"Create a new IAM role for the {len(production_impacts)} affected production service(s)",
                    rationale="Separate concerns and allow safe migration",
                    estimated_time="10 minutes"
                ))
                
                steps.append(RecommendedStep(
                    order=2,
                    action="migrate_services",
                    description="Migrate affected services to the new role",
                    rationale="Move workloads off the role being modified",
                    estimated_time="1 hour"
                ))
                
                steps.append(RecommendedStep(
                    order=3,
                    action="verify_access",
                    description="Verify 24 hours of successful access from new role",
                    rationale="Ensure migration is complete and stable",
                    estimated_time="24 hours"
                ))
                
                steps.append(RecommendedStep(
                    order=4,
                    action="apply_change",
                    description="Apply the original IAM change",
                    rationale="Now safe since dependent services have migrated",
                    estimated_time="5 minutes"
                ))
        
        return steps
    
    @staticmethod
    def _build_warnings(impacts: List[Impact]) -> List[str]:
        """Build warning messages for critical findings."""
        warnings = []
        
        critical_impacts = [i for i in impacts if i.impact_level == ImpactLevel.CRITICAL]
        if critical_impacts:
            warnings.append(
                f"CRITICAL: {len(critical_impacts)} production service(s) will be impacted. "
                "Do not deploy without migration plan."
            )
        
        high_impacts = [i for i in impacts if i.impact_level == ImpactLevel.HIGH]
        if high_impacts:
            warnings.append(
                f"HIGH: {len(high_impacts)} service(s) with frequent usage will be affected."
            )
        
        return warnings
    
    @staticmethod
    def _build_summary(impacts: List[Impact], overall_impact: ImpactLevel) -> str:
        """Build a human-readable summary."""
        if not impacts:
            return "No production impact detected. This change appears safe to deploy."
        
        production_count = sum(1 for i in impacts if i.service.environment == "production")
        
        if overall_impact == ImpactLevel.CRITICAL:
            return (
                f"This change will break {production_count} production service(s). "
                "Recommend creating new roles and migrating services before applying this change."
            )
        elif overall_impact == ImpactLevel.HIGH:
            return (
                f"This change will affect {production_count} production service(s). "
                "Recommend staged rollout with verification at each step."
            )
        elif overall_impact == ImpactLevel.MEDIUM:
            return (
                f"This change may affect {production_count} service(s). "
                "Recommend testing in staging before production deployment."
            )
        else:
            return "No significant impact detected."
