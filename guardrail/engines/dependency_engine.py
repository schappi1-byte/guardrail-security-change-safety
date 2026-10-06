"""Dependency graph engine for tracing IAM role usage."""

from typing import List, Dict, Set, Optional
from guardrail.models.types import (
    ServiceDependency, IAMChange, IAMPermission, Impact, 
    UsageEvidence, ImpactLevel, ConfidenceLevel
)


class DependencyGraph:
    """Maps IAM roles to dependent services and resources."""
    
    def __init__(self):
        self.role_to_services: Dict[str, List[ServiceDependency]] = {}
        self.service_to_usage: Dict[str, List[UsageEvidence]] = {}
    
    def add_role_dependency(self, role_name: str, service: ServiceDependency) -> None:
        """Register a service that depends on an IAM role."""
        if role_name not in self.role_to_services:
            self.role_to_services[role_name] = []
        self.role_to_services[role_name].append(service)
    
    def add_usage_evidence(self, service_name: str, usage: UsageEvidence) -> None:
        """Record observed usage evidence for a service."""
        if service_name not in self.service_to_usage:
            self.service_to_usage[service_name] = []
        self.service_to_usage[service_name].append(usage)
    
    def find_impacted_services(self, change: IAMChange) -> List[Impact]:
        """Find all services impacted by an IAM change."""
        impacted = []
        
        # Find all services using this role
        affected_services = self.role_to_services.get(change.role_name, [])
        
        # For each affected service, check if the permissions being removed are used
        for service in affected_services:
            for removed_perm in change.permissions_removed:
                # Look for usage evidence matching this permission
                usage_evidence = self._find_matching_usage(
                    service.service_name, 
                    removed_perm
                )
                
                if usage_evidence:
                    impact = Impact(
                        service=service,
                        affected_permissions=[removed_perm],
                        evidence=usage_evidence,
                        impact_level=self._assess_impact_level(service, usage_evidence),
                        confidence=usage_evidence.confidence,
                        reason=f"{service.service_name} actively uses {removed_perm.action} on {removed_perm.resource}"
                    )
                    impacted.append(impact)
                else:
                    # No direct evidence but could still impact the service
                    impact = Impact(
                        service=service,
                        affected_permissions=[removed_perm],
                        evidence=None,
                        impact_level=ImpactLevel.MEDIUM,
                        confidence=ConfidenceLevel.MEDIUM,
                        reason=f"{service.service_name} assumes role {change.role_name} which is losing {removed_perm.action}"
                    )
                    impacted.append(impact)
        
        return impacted
    
    def _find_matching_usage(self, service_name: str, permission: IAMPermission) -> Optional[UsageEvidence]:
        """Find usage evidence matching a specific permission."""
        usages = self.service_to_usage.get(service_name, [])
        
        for usage in usages:
            if self._action_matches(usage.action, permission.action):
                if self._resource_matches(usage.resource, permission.resource):
                    return usage
        
        return None
    
    @staticmethod
    def _action_matches(used_action: str, permission_action: str) -> bool:
        """Check if a used action matches a permission action."""
        if permission_action == "*":
            return True
        
        # Handle wildcards in permission action
        if permission_action.endswith("*"):
            prefix = permission_action[:-1]
            return used_action.startswith(prefix)
        
        return used_action == permission_action
    
    @staticmethod
    def _resource_matches(used_resource: str, permission_resource: str) -> bool:
        """Check if a used resource matches a permission resource."""
        if permission_resource == "*":
            return True
        
        # Handle wildcards
        if permission_resource.endswith("*"):
            prefix = permission_resource[:-1]
            return used_resource.startswith(prefix)
        
        return used_resource == permission_resource
    
    @staticmethod
    def _assess_impact_level(service: ServiceDependency, usage: UsageEvidence) -> ImpactLevel:
        """Assess the impact level based on service environment and usage frequency."""
        if service.environment == "production":
            if usage.count > 100:
                return ImpactLevel.CRITICAL
            elif usage.count > 10:
                return ImpactLevel.HIGH
            else:
                return ImpactLevel.MEDIUM
        elif service.environment == "staging":
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW
