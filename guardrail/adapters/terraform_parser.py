"""Parser for Terraform IAM changes."""

import re
from typing import List, Dict, Optional
from guardrail.models.types import IAMChange, IAMPermission


class TerraformParser:
    """Parses Terraform diffs to extract IAM changes."""

    @staticmethod
    def parse_terraform_diff(diff_content: str) -> List[IAMChange]:
        """
        Parse a Terraform diff and extract IAM policy changes.
        
        Args:
            diff_content: The raw diff output from Terraform or git
            
        Returns:
            List of IAMChange objects representing the changes
        """
        changes = []
        
        # Find all resource blocks (handles aws_iam_role_policy and similar)
        resource_pattern = r'resource "aws_iam[a-z_]*" "([^"]+)"'
        resources = re.finditer(resource_pattern, diff_content)
        
        for resource_match in resources:
            role_name = resource_match.group(1)
            
            # Get the section for this resource - find from start to next resource or end
            start = resource_match.start()
            next_resource = re.search(r'\nresource "', diff_content[start + 10:])
            if next_resource:
                end = start + 10 + next_resource.start()
            else:
                end = len(diff_content)
            
            resource_section = diff_content[start:end]
            
            change = IAMChange(role_name=role_name)
            
            # Parse removed permissions (lines starting with -)
            removed_perms = TerraformParser._extract_permissions(resource_section, removed=True)
            change.permissions_removed = removed_perms
            
            # Parse added permissions (lines starting with +)
            added_perms = TerraformParser._extract_permissions(resource_section, added=True)
            change.permissions_added = added_perms
            
            if added_perms or removed_perms:
                changes.append(change)
        
        return changes

    @staticmethod
    def _extract_role_name(resource_block: str) -> Optional[str]:
        """Extract the role name from a Terraform resource block."""
        match = re.search(r'_role["\']?\s+["\'](\w+)["\']', resource_block)
        if match:
            return match.group(1)
        
        # Try alternate patterns
        match = re.search(r'resource "aws_iam_role_policy["\']?\s+["\'](\w+)["\']', resource_block)
        if match:
            return match.group(1)
        
        return None

    @staticmethod
    def _extract_permissions(block: str, added: bool = False, removed: bool = False) -> List[IAMPermission]:
        """Extract IAM permissions from a block."""
        permissions = []
        
        # Split into lines
        lines = block.split('\n')
        
        for i, line in enumerate(lines):
            # Check if this is a removed or added line
            is_removed_line = line.lstrip().startswith('-')
            is_added_line = line.lstrip().startswith('+')
            
            # Match type
            if removed and not is_removed_line:
                continue
            if added and not is_added_line:
                continue
            
            # Check for Actions/actions field
            if 'Actions' not in line and 'actions' not in line:
                continue
            
            # Extract all quoted strings (these are actions)
            action_matches = re.findall(r'"([^"]+)"', line)
            
            for action in action_matches:
                if action and ':' in action:  # S3:GetObject format
                    # Look for resource in nearby lines
                    resource = "*"
                    for j in range(max(0, i-5), min(len(lines), i+5)):
                        if 'Resource' in lines[j] or 'resource' in lines[j]:
                            res_match = re.search(r'arn:aws:[a-z0-9:*/-]+', lines[j])
                            if res_match:
                                resource = res_match.group(0)
                                break
                    
                    permissions.append(IAMPermission(
                        action=action,
                        resource=resource,
                        effect="Allow"
                    ))
        
        return permissions

    @staticmethod
    def summarize_change(change: IAMChange) -> str:
        """Generate a human-readable summary of an IAM change."""
        summary = f"Role: {change.role_name}\n"
        
        if change.permissions_removed:
            summary += f"  Removed: {len(change.permissions_removed)} permission(s)\n"
            for perm in change.permissions_removed[:3]:  # Show first 3
                summary += f"    - {perm.action} on {perm.resource}\n"
        
        if change.permissions_added:
            summary += f"  Added: {len(change.permissions_added)} permission(s)\n"
            for perm in change.permissions_added[:3]:  # Show first 3
                summary += f"    + {perm.action} on {perm.resource}\n"
        
        return summary
