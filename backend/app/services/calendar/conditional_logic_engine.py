# Advanced Conditional Logic Engine - Phase B Sprint 2 Day 6
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta, date, time
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging
from enum import Enum
import re
import ast
import operator

logger = logging.getLogger(__name__)

class ConditionOperator(Enum):
    """Conditional operators"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"

class LogicalOperator(Enum):
    """Logical operators for combining conditions"""
    AND = "and"
    OR = "or"
    NOT = "not"

class ConditionType(Enum):
    """Types of conditions"""
    SIMPLE = "simple"
    COMPOUND = "compound"
    FUNCTION = "function"
    SCRIPT = "script"

@dataclass
class Condition:
    """Individual condition definition"""
    condition_id: str
    name: str
    condition_type: ConditionType
    field_path: str  # e.g., "compliance.overall_score", "user.department"
    operator: ConditionOperator
    value: Any
    description: str
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class CompoundCondition:
    """Compound condition with multiple conditions"""
    condition_id: str
    name: str
    logical_operator: LogicalOperator
    conditions: List[Union[Condition, 'CompoundCondition']]
    description: str
    enabled: bool = True

@dataclass
class ConditionalRule:
    """Complete conditional rule with actions"""
    rule_id: str
    name: str
    description: str
    condition: Union[Condition, CompoundCondition]
    actions: List[Dict[str, Any]]
    priority: int = 100
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_evaluated: Optional[datetime] = None
    evaluation_count: int = 0

@dataclass
class EvaluationContext:
    """Context for condition evaluation"""
    timestamp: datetime
    user_data: Dict[str, Any]
    compliance_data: Dict[str, Any]
    quality_data: Dict[str, Any]
    training_data: Dict[str, Any]
    system_data: Dict[str, Any]
    custom_data: Dict[str, Any]

@dataclass
class EvaluationResult:
    """Result of condition evaluation"""
    rule_id: str
    result: bool
    evaluation_time_ms: int
    context_used: Dict[str, Any]
    conditions_evaluated: List[Dict[str, Any]]
    actions_triggered: List[Dict[str, Any]]
    error_message: Optional[str] = None

class ConditionalLogicEngine:
    """
    Advanced Conditional Logic Engine
    Complex business rule evaluation for delivery scheduling and automation
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Operator mapping
        self.operators = {
            ConditionOperator.EQUALS: operator.eq,
            ConditionOperator.NOT_EQUALS: operator.ne,
            ConditionOperator.GREATER_THAN: operator.gt,
            ConditionOperator.GREATER_EQUAL: operator.ge,
            ConditionOperator.LESS_THAN: operator.lt,
            ConditionOperator.LESS_EQUAL: operator.le,
            ConditionOperator.CONTAINS: lambda a, b: b in a,
            ConditionOperator.NOT_CONTAINS: lambda a, b: b not in a,
            ConditionOperator.IN: lambda a, b: a in b,
            ConditionOperator.NOT_IN: lambda a, b: a not in b,
            ConditionOperator.IS_NULL: lambda a, b: a is None,
            ConditionOperator.IS_NOT_NULL: lambda a, b: a is not None,
        }
        
        # Function registry
        self.functions = self._register_functions()
        
        # Evaluation cache
        self.evaluation_cache: Dict[str, EvaluationResult] = {}
        
    async def evaluate_rule(self, 
                           rule: ConditionalRule,
                           context: EvaluationContext) -> EvaluationResult:
        """Evaluate a conditional rule against context"""
        
        start_time = datetime.now()
        
        logger.debug(f"Evaluating rule: {rule.name}")
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(rule, context)
            
            # Check cache for recent evaluation
            if cache_key in self.evaluation_cache:
                cached_result = self.evaluation_cache[cache_key]
                # Use cached result if less than 5 minutes old
                if (start_time - cached_result.context_used.get('timestamp', start_time)).total_seconds() < 300:
                    logger.debug(f"Using cached result for rule: {rule.name}")
                    return cached_result
            
            # Evaluate condition
            condition_result, conditions_evaluated = await self._evaluate_condition(rule.condition, context)
            
            # Execute actions if condition is true
            actions_triggered = []
            if condition_result:
                actions_triggered = await self._execute_rule_actions(rule.actions, context)
            
            # Calculate evaluation time
            evaluation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Create result
            result = EvaluationResult(
                rule_id=rule.rule_id,
                result=condition_result,
                evaluation_time_ms=evaluation_time,
                context_used={
                    'timestamp': start_time,
                    'user_id': context.user_data.get('id'),
                    'compliance_score': context.compliance_data.get('overall_score'),
                    'context_hash': hash(str(context.__dict__))
                },
                conditions_evaluated=conditions_evaluated,
                actions_triggered=actions_triggered
            )
            
            # Cache result
            self.evaluation_cache[cache_key] = result
            
            # Update rule statistics
            rule.last_evaluated = start_time
            rule.evaluation_count += 1
            
            logger.debug(f"Rule evaluation completed: {rule.name} = {condition_result}")
            
            return result
            
        except Exception as e:
            evaluation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.error(f"Rule evaluation failed for {rule.name}: {str(e)}")
            
            return EvaluationResult(
                rule_id=rule.rule_id,
                result=False,
                evaluation_time_ms=evaluation_time,
                context_used={'error': 'evaluation_failed'},
                conditions_evaluated=[],
                actions_triggered=[],
                error_message=str(e)
            )
    
    async def evaluate_multiple_rules(self, 
                                    rules: List[ConditionalRule],
                                    context: EvaluationContext) -> List[EvaluationResult]:
        """Evaluate multiple rules with priority ordering"""
        
        # Sort rules by priority (lower number = higher priority)
        sorted_rules = sorted(rules, key=lambda r: r.priority)
        
        results = []
        
        # Evaluate rules in priority order
        for rule in sorted_rules:
            if rule.enabled:
                result = await self.evaluate_rule(rule, context)
                results.append(result)
                
                # Stop evaluation if a high-priority rule triggers critical action
                if (result.result and 
                    rule.priority < 50 and  # High priority
                    any(action.get('type') == 'stop_evaluation' for action in result.actions_triggered)):
                    break
        
        return results
    
    async def _evaluate_condition(self, 
                                condition: Union[Condition, CompoundCondition],
                                context: EvaluationContext) -> tuple[bool, List[Dict[str, Any]]]:
        """Evaluate a single condition or compound condition"""
        
        conditions_evaluated = []
        
        if isinstance(condition, Condition):
            result = await self._evaluate_simple_condition(condition, context)
            conditions_evaluated.append({
                'condition_id': condition.condition_id,
                'type': 'simple',
                'result': result,
                'field_path': condition.field_path,
                'operator': condition.operator.value,
                'value': condition.value
            })
            return result, conditions_evaluated
            
        elif isinstance(condition, CompoundCondition):
            # Evaluate all sub-conditions
            sub_results = []
            
            for sub_condition in condition.conditions:
                sub_result, sub_conditions = await self._evaluate_condition(sub_condition, context)
                sub_results.append(sub_result)
                conditions_evaluated.extend(sub_conditions)
            
            # Apply logical operator
            if condition.logical_operator == LogicalOperator.AND:
                result = all(sub_results)
            elif condition.logical_operator == LogicalOperator.OR:
                result = any(sub_results)
            elif condition.logical_operator == LogicalOperator.NOT:
                result = not sub_results[0] if sub_results else False
            else:
                result = False
            
            conditions_evaluated.append({
                'condition_id': condition.condition_id,
                'type': 'compound',
                'result': result,
                'logical_operator': condition.logical_operator.value,
                'sub_conditions_count': len(condition.conditions)
            })
            
            return result, conditions_evaluated
        
        return False, conditions_evaluated
    
    async def _evaluate_simple_condition(self, 
                                       condition: Condition,
                                       context: EvaluationContext) -> bool:
        """Evaluate a simple condition"""
        
        try:
            # Get field value from context
            field_value = self._get_field_value(condition.field_path, context)
            
            # Handle special operators
            if condition.operator == ConditionOperator.IS_NULL:
                return field_value is None
            elif condition.operator == ConditionOperator.IS_NOT_NULL:
                return field_value is not None
            elif condition.operator == ConditionOperator.REGEX:
                if isinstance(field_value, str) and isinstance(condition.value, str):
                    return bool(re.search(condition.value, field_value))
                return False
            elif condition.operator == ConditionOperator.BETWEEN:
                if isinstance(condition.value, (list, tuple)) and len(condition.value) == 2:
                    return condition.value[0] <= field_value <= condition.value[1]
                return False
            elif condition.operator == ConditionOperator.NOT_BETWEEN:
                if isinstance(condition.value, (list, tuple)) and len(condition.value) == 2:
                    return not (condition.value[0] <= field_value <= condition.value[1])
                return False
            
            # Handle standard operators
            op_func = self.operators.get(condition.operator)
            if op_func:
                return op_func(field_value, condition.value)
            
            return False
            
        except Exception as e:
            logger.error(f"Condition evaluation failed: {condition.name} - {str(e)}")
            return False
    
    def _get_field_value(self, field_path: str, context: EvaluationContext) -> Any:
        """Get field value from context using dot notation"""
        
        path_parts = field_path.split('.')
        
        # Map context sections
        context_map = {
            'user': context.user_data,
            'compliance': context.compliance_data,
            'quality': context.quality_data,
            'training': context.training_data,
            'system': context.system_data,
            'custom': context.custom_data,
            'timestamp': context.timestamp
        }
        
        # Start with appropriate context section
        if path_parts[0] in context_map:
            current_value = context_map[path_parts[0]]
            path_parts = path_parts[1:]
        else:
            # Try to find in any context section
            current_value = None
            for context_section in context_map.values():
                if isinstance(context_section, dict) and path_parts[0] in context_section:
                    current_value = context_section
                    break
        
        # Navigate the path
        for part in path_parts:
            if isinstance(current_value, dict):
                current_value = current_value.get(part)
            elif hasattr(current_value, part):
                current_value = getattr(current_value, part)
            else:
                return None
        
        return current_value
    
    async def _execute_rule_actions(self, 
                                  actions: List[Dict[str, Any]],
                                  context: EvaluationContext) -> List[Dict[str, Any]]:
        """Execute actions triggered by rule evaluation"""
        
        executed_actions = []
        
        for action in actions:
            try:
                action_type = action.get('type')
                action_params = action.get('parameters', {})
                
                if action_type == 'modify_delivery_time':
                    result = await self._action_modify_delivery_time(action_params, context)
                elif action_type == 'change_recipients':
                    result = await self._action_change_recipients(action_params, context)
                elif action_type == 'escalate_notification':
                    result = await self._action_escalate_notification(action_params, context)
                elif action_type == 'skip_delivery':
                    result = await self._action_skip_delivery(action_params, context)
                elif action_type == 'add_approval_required':
                    result = await self._action_add_approval_required(action_params, context)
                elif action_type == 'set_priority':
                    result = await self._action_set_priority(action_params, context)
                elif action_type == 'log_event':
                    result = await self._action_log_event(action_params, context)
                elif action_type == 'stop_evaluation':
                    result = {'action': 'stop_evaluation', 'executed': True}
                else:
                    result = {'action': action_type, 'executed': False, 'error': 'Unknown action type'}
                
                executed_actions.append({
                    'action_type': action_type,
                    'parameters': action_params,
                    'result': result,
                    'executed_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Action execution failed: {action.get('type')} - {str(e)}")
                executed_actions.append({
                    'action_type': action.get('type'),
                    'parameters': action_params,
                    'result': {'executed': False, 'error': str(e)},
                    'executed_at': datetime.now().isoformat()
                })
        
        return executed_actions
    
    async def _action_modify_delivery_time(self, 
                                         params: Dict[str, Any],
                                         context: EvaluationContext) -> Dict[str, Any]:
        """Modify delivery time based on conditions"""
        
        modification_type = params.get('type', 'delay')
        amount = params.get('amount', 1)
        unit = params.get('unit', 'hours')
        
        if modification_type == 'delay':
            if unit == 'hours':
                new_time = context.timestamp + timedelta(hours=amount)
            elif unit == 'days':
                new_time = context.timestamp + timedelta(days=amount)
            elif unit == 'business_days':
                # Would integrate with business calendar service
                new_time = context.timestamp + timedelta(days=amount * 1.4)  # Approximate
            else:
                new_time = context.timestamp
        elif modification_type == 'advance':
            if unit == 'hours':
                new_time = context.timestamp - timedelta(hours=amount)
            elif unit == 'days':
                new_time = context.timestamp - timedelta(days=amount)
            else:
                new_time = context.timestamp
        else:
            new_time = context.timestamp
        
        return {
            'action': 'modify_delivery_time',
            'original_time': context.timestamp.isoformat(),
            'new_time': new_time.isoformat(),
            'modification': f"{modification_type} {amount} {unit}",
            'executed': True
        }
    
    async def _action_change_recipients(self, 
                                      params: Dict[str, Any],
                                      context: EvaluationContext) -> Dict[str, Any]:
        """Change delivery recipients based on conditions"""
        
        operation = params.get('operation', 'add')
        recipients = params.get('recipients', [])
        
        current_recipients = context.custom_data.get('recipients', [])
        
        if operation == 'add':
            new_recipients = list(set(current_recipients + recipients))
        elif operation == 'remove':
            new_recipients = [r for r in current_recipients if r not in recipients]
        elif operation == 'replace':
            new_recipients = recipients
        else:
            new_recipients = current_recipients
        
        return {
            'action': 'change_recipients',
            'operation': operation,
            'original_recipients': current_recipients,
            'new_recipients': new_recipients,
            'executed': True
        }
    
    async def _action_escalate_notification(self, 
                                          params: Dict[str, Any],
                                          context: EvaluationContext) -> Dict[str, Any]:
        """Escalate notification to higher authority"""
        
        escalation_level = params.get('level', 'supervisor')
        reason = params.get('reason', 'Conditional escalation triggered')
        
        escalation_recipients = {
            'supervisor': ['supervisor@company.com'],
            'manager': ['manager@company.com'],
            'director': ['director@company.com'],
            'executive': ['ceo@company.com', 'cfo@company.com']
        }
        
        recipients = escalation_recipients.get(escalation_level, [])
        
        return {
            'action': 'escalate_notification',
            'escalation_level': escalation_level,
            'recipients': recipients,
            'reason': reason,
            'executed': True
        }
    
    def _register_functions(self) -> Dict[str, Callable]:
        """Register available functions for conditional logic"""
        
        return {
            'now': lambda: datetime.now(),
            'today': lambda: date.today(),
            'is_business_day': self._func_is_business_day,
            'days_between': self._func_days_between,
            'compliance_threshold': self._func_compliance_threshold,
            'user_in_department': self._func_user_in_department,
            'has_role': self._func_has_role,
            'count_open_issues': self._func_count_open_issues,
            'average_score': self._func_average_score
        }
    
    def _func_is_business_day(self, target_date: date) -> bool:
        """Function to check if date is a business day"""
        # Would integrate with business calendar service
        return target_date.weekday() < 5  # Monday-Friday
    
    def _func_days_between(self, start_date: date, end_date: date) -> int:
        """Function to calculate days between dates"""
        return (end_date - start_date).days
    
    def _func_compliance_threshold(self, score: float, threshold: float) -> bool:
        """Function to check compliance threshold"""
        return score >= threshold
    
    def _generate_cache_key(self, rule: ConditionalRule, context: EvaluationContext) -> str:
        """Generate cache key for rule evaluation"""
        
        import hashlib
        
        key_data = {
            'rule_id': rule.rule_id,
            'context_hash': hash(str(context.__dict__)),
            'timestamp_hour': context.timestamp.replace(minute=0, second=0, microsecond=0)
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return f"rule_eval:{hashlib.md5(key_string.encode()).hexdigest()}"

# Factory function
def create_conditional_logic_engine(db: Session) -> ConditionalLogicEngine:
    """Create and configure conditional logic engine"""
    return ConditionalLogicEngine(db=db)