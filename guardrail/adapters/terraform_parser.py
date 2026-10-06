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
        
        # Split into resource blocks
        resource_blocks = re.split(r'resource "aws_iam', diff_content)
        
        for block in resource_blocks[1:]:  # Skip the first empty split
            role_name = TerraformParser._extract_role_name(block)
            if not role_name:
                continue
            
            change = IAMChange(role_name=role_name)
            
            # Parse added permissions
            added_perms = TerraformParser._extract_permissions(block, added=True)
            change.permissions_added = added_perms
            
            # Parse removed permissions
            removed_perms = TerraformParser._extract_permissions(block, removed=True)
            change.permissions_removed = removed_perms
            
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
        
        # Pattern for actions
        action_pattern = r'actions\s*=\s*\[(.*?)\]'
        
        if added:
            # Look for + lines
            lines = [line for line in block.split('\n') if line.strip().startswith('+')]
        elif removed:
            # Look for - lines
            lines = [line for line in block.split('\n') if line.strip().startswith('-')]
        else:
            lines = block.split('\n')
        
        for line in lines:
            # Extract action strings
            if '"s3:' in line or '"iam:' in line or '"ec2:' in line:
                action_matches = re.findall(r'"([a-z0-9:*]+)"', line)
                for action in action_matches:
                    # Extract resource
                    resource_match = re.search(r'arn:aws:[a-z0-9:*/-]+', line)
                    resource = resource_match.group(0) if resource_match else "*"
                    
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
