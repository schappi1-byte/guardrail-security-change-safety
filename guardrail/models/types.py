"""Data types and models for Guardrail security change impact analysis."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from enum import Enum


class ImpactLevel(str, Enum):
    """Impact severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    """Confidence in the impact assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class IAMPermission:
    """Represents an IAM permission/action."""
    action: str
    resource: str
    effect: Literal["Allow", "Deny"] = "Allow"


@dataclass
class IAMChange:
    """Represents a change to IAM policy."""
    role_name: str
    permissions_added: List[IAMPermission] = field(default_factory=list)
    permissions_removed: List[IAMPermission] = field(default_factory=list)
    permissions_modified: List[Dict] = field(default_factory=list)


@dataclass
class ServiceDependency:
    """A service that depends on an IAM role."""
    service_name: str
    namespace: str
    environment: Literal["production", "staging", "development"] = "production"
    role_arn: str = ""
    service_account: str = ""


@dataclass
class UsageEvidence:
    """Evidence of actual usage from CloudTrail or other sources."""
    service_name: str
    action: str
    resource: str
    count: int
    last_seen: str
    date_range: str
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH


@dataclass
class Impact:
    """Impact of a security change on a specific service."""
    service: ServiceDependency
    affected_permissions: List[IAMPermission]
    evidence: Optional[UsageEvidence] = None
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    reason: str = ""


@dataclass
class RecommendedStep:
    """A recommended step for safer change rollout."""
    order: int
    action: str
    description: str
    rationale: str
    estimated_time: str = "variable"


@dataclass
class SecurityChangeImpactReport:
    """Complete impact analysis report."""
    change_id: str
    terraform_change_summary: str
    iam_changes: List[IAMChange]
    impacts: List[Impact]
    overall_impact: ImpactLevel
    confidence: ConfidenceLevel
    recommendation_summary: str
    recommended_steps: List[RecommendedStep]
    safe_to_deploy: bool
    warnings: List[str] = field(default_factory=list)
