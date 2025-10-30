# Dynamic Recipient Management - Phase B Sprint 2 Day 6
from typing import Dict, List, Any, Optional, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class RecipientType(Enum):
    """Types of recipients"""
    USER = "user"
    ROLE = "role"
    DEPARTMENT = "department"
    GROUP = "group"
    DISTRIBUTION_LIST = "distribution_list"
    EXTERNAL = "external"
    DYNAMIC = "dynamic"

class SelectionCriteria(Enum):
    """Criteria for dynamic recipient selection"""
    DEPARTMENT = "department"
    ROLE = "role"
    COMPLIANCE_SCORE = "compliance_score"
    TRAINING_STATUS = "training_status"
    LOCATION = "location"
    SHIFT = "shift"
    AVAILABILITY = "availability"
    EXPERTISE = "expertise"
    CLEARANCE_LEVEL = "clearance_level"

@dataclass
class RecipientRule:
    """Rule for dynamic recipient selection"""
    rule_id: str
    name: str
    description: str
    criteria: SelectionCriteria
    conditions: Dict[str, Any]
    include_managers: bool = False
    exclude_on_leave: bool = True
    priority: int = 100
    enabled: bool = True

@dataclass
class RecipientGroup:
    """Recipient group definition"""
    group_id: str
    name: str
    description: str
    members: List[str]
    rules: List[RecipientRule]
    auto_update: bool = True
    last_updated: datetime = field(default_factory=datetime.now)
    update_frequency_hours: int = 24

@dataclass
class DistributionList:
    """Distribution list with dynamic membership"""
    list_id: str
    name: str
    description: str
    owner: str
    recipients: List[str]
    dynamic_rules: List[RecipientRule]
    fallback_recipients: List[str]
    auto_expand: bool = True
    include_escalation_chain: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class RecipientContext:
    """Context for recipient selection"""
    report_type: str
    priority: str
    compliance_score: Optional[float]
    department: Optional[str]
    event_type: Optional[str]
    timestamp: datetime
    custom_attributes: Dict[str, Any]

class DynamicRecipientService:
    """
    Dynamic Recipient Management Service
    Intelligent recipient selection based on roles, context, and business rules
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Recipient configurations
        self.distribution_lists = self._load_distribution_lists()
        self.recipient_groups = self._load_recipient_groups()
        
        # Organization data cache
        self.organization_cache = {}
        self.cache_expiry = datetime.now()
        
    async def resolve_recipients(self, 
                               recipient_specs: List[str],
                               context: RecipientContext) -> List[str]:
        """
        Resolve recipient specifications to actual email addresses
        
        Args:
            recipient_specs: List of recipient specifications (emails, roles, groups, etc.)
            context: Context for dynamic resolution
            
        Returns:
            List of resolved email addresses
        """
        
        logger.info(f"Resolving {len(recipient_specs)} recipient specifications")
        
        resolved_recipients = set()
        
        for spec in recipient_specs:
            try:
                if self._is_email_address(spec):
                    # Direct email address
                    resolved_recipients.add(spec)
                    
                elif spec.startswith('role:'):
                    # Role-based selection
                    role_recipients = await self._resolve_role_recipients(spec[5:], context)
                    resolved_recipients.update(role_recipients)
                    
                elif spec.startswith('dept:'):
                    # Department-based selection
                    dept_recipients = await self._resolve_department_recipients(spec[5:], context)
                    resolved_recipients.update(dept_recipients)
                    
                elif spec.startswith('group:'):
                    # Group-based selection
                    group_recipients = await self._resolve_group_recipients(spec[6:], context)
                    resolved_recipients.update(group_recipients)
                    
                elif spec.startswith('list:'):
                    # Distribution list
                    list_recipients = await self._resolve_distribution_list(spec[5:], context)
                    resolved_recipients.update(list_recipients)
                    
                elif spec.startswith('dynamic:'):
                    # Dynamic rule-based selection
                    dynamic_recipients = await self._resolve_dynamic_recipients(spec[8:], context)
                    resolved_recipients.update(dynamic_recipients)
                    
                elif spec.startswith('escalation:'):
                    # Escalation chain
                    escalation_recipients = await self._resolve_escalation_chain(spec[11:], context)
                    resolved_recipients.update(escalation_recipients)
                    
                else:
                    # Try to resolve as user or fallback
                    fallback_recipients = await self._resolve_fallback(spec, context)
                    resolved_recipients.update(fallback_recipients)
                    
            except Exception as e:
                logger.error(f"Failed to resolve recipient spec '{spec}': {str(e)}")
        
        # Filter and validate final list
        final_recipients = await self._filter_and_validate_recipients(
            list(resolved_recipients), context
        )
        
        logger.info(f"Resolved to {len(final_recipients)} final recipients")
        
        return final_recipients
    
    async def create_distribution_list(self, 
                                     list_config: Dict[str, Any]) -> DistributionList:
        """Create a new distribution list"""
        
        distribution_list = DistributionList(
            list_id=list_config['list_id'],
            name=list_config['name'],
            description=list_config['description'],
            owner=list_config['owner'],
            recipients=list_config.get('recipients', []),
            dynamic_rules=[],
            fallback_recipients=list_config.get('fallback_recipients', []),
            auto_expand=list_config.get('auto_expand', True),
            include_escalation_chain=list_config.get('include_escalation_chain', False)
        )
        
        # Parse dynamic rules
        for rule_config in list_config.get('dynamic_rules', []):
            rule = RecipientRule(
                rule_id=rule_config['rule_id'],
                name=rule_config['name'],
                description=rule_config['description'],
                criteria=SelectionCriteria(rule_config['criteria']),
                conditions=rule_config['conditions'],
                include_managers=rule_config.get('include_managers', False),
                exclude_on_leave=rule_config.get('exclude_on_leave', True),
                priority=rule_config.get('priority', 100),
                enabled=rule_config.get('enabled', True)
            )
            distribution_list.dynamic_rules.append(rule)
        
        # Store in database
        await self._store_distribution_list(distribution_list)
        
        # Add to cache
        self.distribution_lists.append(distribution_list)
        
        logger.info(f"Created distribution list: {distribution_list.name}")
        
        return distribution_list
    
    async def update_distribution_list_membership(self, list_id: str) -> Dict[str, Any]:
        """Update distribution list membership based on dynamic rules"""
        
        dist_list = self._get_distribution_list(list_id)
        if not dist_list:
            raise ValueError(f"Distribution list {list_id} not found")
        
        if not dist_list.auto_expand:
            return {'updated': False, 'reason': 'auto_expand disabled'}
        
        logger.info(f"Updating membership for distribution list: {dist_list.name}")
        
        # Create context for evaluation
        context = RecipientContext(
            report_type='membership_update',
            priority='normal',
            compliance_score=None,
            department=None,
            event_type='membership_update',
            timestamp=datetime.now(),
            custom_attributes={}
        )
        
        # Resolve dynamic recipients
        dynamic_recipients = set()
        for rule in dist_list.dynamic_rules:
            if rule.enabled:
                rule_recipients = await self._apply_recipient_rule(rule, context)
                dynamic_recipients.update(rule_recipients)
        
        # Combine with static recipients
        all_recipients = set(dist_list.recipients) | dynamic_recipients
        
        # Update the list
        original_count = len(dist_list.recipients)
        dist_list.recipients = list(all_recipients)
        dist_list.last_updated = datetime.now()
        
        # Store updates
        await self._store_distribution_list(dist_list)
        
        return {
            'updated': True,
            'original_count': original_count,
            'new_count': len(dist_list.recipients),
            'added': len(all_recipients) - original_count,
            'dynamic_rules_applied': len([r for r in dist_list.dynamic_rules if r.enabled])
        }
    
    async def _resolve_role_recipients(self, role: str, context: RecipientContext) -> List[str]:
        """Resolve recipients based on role"""
        
        await self._refresh_organization_cache()
        
        role_query = """
            SELECT u.email, u.full_name, u.department
            FROM users u
            WHERE u.role = :role
            AND u.is_active = true
            AND u.is_deleted = false
        """
        
        result = self.db.execute(text(role_query), {'role': role})
        recipients = [row.email for row in result.fetchall()]
        
        # Apply context-based filtering
        filtered_recipients = await self._apply_context_filtering(recipients, context)
        
        return filtered_recipients
    
    async def _resolve_department_recipients(self, department: str, context: RecipientContext) -> List[str]:
        """Resolve recipients based on department"""
        
        await self._refresh_organization_cache()
        
        # Base query for department members
        dept_query = """
            SELECT u.email, u.full_name, u.role, u.manager_email
            FROM users u
            WHERE u.department = :department
            AND u.is_active = true
            AND u.is_deleted = false
        """
        
        result = self.db.execute(text(dept_query), {'department': department})
        recipients = []
        
        for row in result.fetchall():
            recipients.append(row.email)
            
            # Include managers if specified in context
            if (context.custom_attributes.get('include_managers', False) and 
                row.manager_email and 
                row.manager_email not in recipients):
                recipients.append(row.manager_email)
        
        # Apply context-based filtering
        filtered_recipients = await self._apply_context_filtering(recipients, context)
        
        return filtered_recipients
    
    async def _resolve_group_recipients(self, group_id: str, context: RecipientContext) -> List[str]:
        """Resolve recipients from a recipient group"""
        
        group = self._get_recipient_group(group_id)
        if not group:
            logger.warning(f"Recipient group {group_id} not found")
            return []
        
        # Start with static members
        recipients = set(group.members)
        
        # Apply dynamic rules
        for rule in group.rules:
            if rule.enabled:
                rule_recipients = await self._apply_recipient_rule(rule, context)
                recipients.update(rule_recipients)
        
        # Apply context-based filtering
        filtered_recipients = await self._apply_context_filtering(list(recipients), context)
        
        return filtered_recipients
    
    async def _resolve_distribution_list(self, list_id: str, context: RecipientContext) -> List[str]:
        """Resolve recipients from a distribution list"""
        
        dist_list = self._get_distribution_list(list_id)
        if not dist_list:
            logger.warning(f"Distribution list {list_id} not found")
            return []
        
        # Update membership if auto-expand is enabled
        if dist_list.auto_expand:
            await self.update_distribution_list_membership(list_id)
        
        recipients = list(dist_list.recipients)
        
        # Add escalation chain if enabled
        if dist_list.include_escalation_chain:
            escalation_recipients = await self._get_escalation_chain(context)
            recipients.extend(escalation_recipients)
        
        # Use fallback recipients if main list is empty
        if not recipients and dist_list.fallback_recipients:
            recipients = dist_list.fallback_recipients
            logger.info(f"Using fallback recipients for distribution list {list_id}")
        
        return recipients
    
    async def _resolve_dynamic_recipients(self, rule_spec: str, context: RecipientContext) -> List[str]:
        """Resolve recipients using dynamic rule specification"""
        
        # Parse rule specification (e.g., "compliance_score<80", "department=quality")
        try:
            if '=' in rule_spec:
                field, value = rule_spec.split('=', 1)
                conditions = {field: {'operator': 'eq', 'value': value}}
            elif '<' in rule_spec:
                field, value = rule_spec.split('<', 1)
                conditions = {field: {'operator': 'lt', 'value': float(value)}}
            elif '>' in rule_spec:
                field, value = rule_spec.split('>', 1)
                conditions = {field: {'operator': 'gt', 'value': float(value)}}
            else:
                # Default to field existence check
                conditions = {rule_spec: {'operator': 'is_not_null', 'value': None}}
            
            # Create temporary rule
            temp_rule = RecipientRule(
                rule_id=f"dynamic_{rule_spec}",
                name=f"Dynamic rule: {rule_spec}",
                description=f"Dynamically created rule for {rule_spec}",
                criteria=SelectionCriteria.DEPARTMENT,  # Will be overridden
                conditions=conditions,
                enabled=True
            )
            
            return await self._apply_recipient_rule(temp_rule, context)
            
        except Exception as e:
            logger.error(f"Failed to parse dynamic rule '{rule_spec}': {str(e)}")
            return []
    
    async def _apply_recipient_rule(self, rule: RecipientRule, context: RecipientContext) -> List[str]:
        """Apply a recipient rule to get matching recipients"""
        
        recipients = []
        
        try:
            if rule.criteria == SelectionCriteria.DEPARTMENT:
                dept_query = """
                    SELECT u.email FROM users u
                    WHERE u.department = :value
                    AND u.is_active = true AND u.is_deleted = false
                """
                result = self.db.execute(text(dept_query), {
                    'value': rule.conditions.get('department', {}).get('value')
                })
                recipients = [row.email for row in result.fetchall()]
                
            elif rule.criteria == SelectionCriteria.ROLE:
                role_query = """
                    SELECT u.email FROM users u
                    WHERE u.role = :value
                    AND u.is_active = true AND u.is_deleted = false
                """
                result = self.db.execute(text(role_query), {
                    'value': rule.conditions.get('role', {}).get('value')
                })
                recipients = [row.email for row in result.fetchall()]
                
            elif rule.criteria == SelectionCriteria.COMPLIANCE_SCORE:
                # Would integrate with compliance service
                # For now, return based on user metadata
                score_threshold = rule.conditions.get('compliance_score', {}).get('value', 80)
                operator = rule.conditions.get('compliance_score', {}).get('operator', 'gte')
                
                # Simulate compliance-based selection
                all_users_query = """
                    SELECT u.email FROM users u
                    WHERE u.is_active = true AND u.is_deleted = false
                """
                result = self.db.execute(text(all_users_query))
                all_users = [row.email for row in result.fetchall()]
                
                # Apply compliance filtering (simplified)
                if operator == 'lt' and context.compliance_score and context.compliance_score < score_threshold:
                    recipients = all_users[:3]  # Simulate escalation to key personnel
                
            # Apply additional filters
            if rule.exclude_on_leave:
                recipients = await self._exclude_on_leave(recipients)
            
            if rule.include_managers:
                manager_emails = await self._get_managers_for_users(recipients)
                recipients.extend(manager_emails)
            
        except Exception as e:
            logger.error(f"Failed to apply recipient rule {rule.rule_id}: {str(e)}")
        
        return recipients
    
    async def _apply_context_filtering(self, recipients: List[str], context: RecipientContext) -> List[str]:
        """Apply context-based filtering to recipients"""
        
        filtered_recipients = []
        
        for recipient in recipients:
            # Check availability (simplified)
            if await self._is_recipient_available(recipient, context):
                # Check if recipient should receive this type of notification
                if await self._should_receive_notification(recipient, context):
                    filtered_recipients.append(recipient)
        
        return filtered_recipients
    
    async def _is_recipient_available(self, email: str, context: RecipientContext) -> bool:
        """Check if recipient is available to receive notifications"""
        
        # Check user status
        user_query = """
            SELECT u.is_active, u.last_login, u.notification_preferences
            FROM users u
            WHERE u.email = :email AND u.is_deleted = false
        """
        
        result = self.db.execute(text(user_query), {'email': email})
        user_data = result.fetchone()
        
        if not user_data or not user_data.is_active:
            return False
        
        # Check if user has been active recently (within 30 days)
        if user_data.last_login:
            inactive_days = (datetime.now() - user_data.last_login).days
            if inactive_days > 30:
                return False
        
        return True
    
    async def _should_receive_notification(self, email: str, context: RecipientContext) -> bool:
        """Check if recipient should receive this type of notification"""
        
        # Check notification preferences
        prefs_query = """
            SELECT notification_preferences FROM users
            WHERE email = :email AND is_deleted = false
        """
        
        result = self.db.execute(text(prefs_query), {'email': email})
        row = result.fetchone()
        
        if row and row.notification_preferences:
            try:
                prefs = json.loads(row.notification_preferences)
                
                # Check if user has opted out of this type of notification
                if context.report_type in prefs.get('disabled_types', []):
                    return False
                
                # Check priority preferences
                if (context.priority == 'low' and 
                    prefs.get('min_priority', 'normal') in ['normal', 'high', 'urgent']):
                    return False
                    
            except (json.JSONDecodeError, KeyError):
                pass
        
        return True
    
    def _is_email_address(self, text: str) -> bool:
        """Check if text is a valid email address"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, text))
    
    def _get_distribution_list(self, list_id: str) -> Optional[DistributionList]:
        """Get distribution list by ID"""
        return next((dl for dl in self.distribution_lists if dl.list_id == list_id), None)
    
    def _get_recipient_group(self, group_id: str) -> Optional[RecipientGroup]:
        """Get recipient group by ID"""
        return next((rg for rg in self.recipient_groups if rg.group_id == group_id), None)

# Factory function
def create_dynamic_recipient_service(db: Session) -> DynamicRecipientService:
    """Create and configure dynamic recipient service"""
    return DynamicRecipientService(db=db)