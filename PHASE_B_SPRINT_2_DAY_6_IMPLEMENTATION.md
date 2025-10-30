# 📅 Phase B Sprint 2 Day 6 - Advanced Scheduling & Business Calendar Integration

**Phase**: B - Advanced Reporting & Analytics  
**Sprint**: 2 - Report Generation & Compliance  
**Day**: 6 - Advanced Scheduling & Business Calendar Integration  
**Focus**: Business calendar management, advanced conditional logic, escalation workflows, and predictive scheduling

---

## 🎯 **Day 6 Objectives**

### **Primary Goals:**
- [ ] Build comprehensive business calendar system with holiday management
- [ ] Create advanced conditional delivery logic with complex business rules
- [ ] Implement multi-level escalation workflows and approval chains
- [ ] Develop dynamic recipient list management with role-based distribution
- [ ] Create predictive delivery optimization with analytics
- [ ] Build advanced scheduling dashboard with monitoring and control

### **Deliverables:**
- Business calendar service with holiday and business day management
- Advanced conditional logic engine for complex delivery rules
- Multi-level escalation workflows with approval chains
- Dynamic recipient management with organizational integration
- Predictive scheduling analytics with optimization recommendations
- Advanced scheduling dashboard with real-time monitoring

---

## 🏗️ **Building on Days 1-5 Foundation**

### **Existing Infrastructure:**
- ✅ **Report Generation** (Day 1): PDF and Excel generation with professional formatting
- ✅ **Template Processing Pipeline** (Day 2): Data aggregation and chart generation
- ✅ **Regulatory Framework** (Day 3): CFR Part 11, ISO 13485, FDA reporting
- ✅ **Compliance Automation** (Day 4): Real-time monitoring and workflow automation
- ✅ **Scheduled Delivery System** (Day 5): Email integration and basic scheduling

### **Day 6 Advanced Enhancements:**
- 🔜 **Business Calendar System**: Holiday management and business day awareness
- 🔜 **Advanced Conditional Logic**: Complex business rule evaluation engine
- 🔜 **Escalation Workflows**: Multi-level approval and escalation chains
- 🔜 **Dynamic Recipient Management**: Role-based distribution lists
- 🔜 **Predictive Analytics**: AI-powered scheduling optimization
- 🔜 **Advanced Dashboard**: Real-time scheduling monitoring and control

---

## 📅 **Business Calendar System**

### **Comprehensive Calendar Management**

#### **Business Calendar Service**
```python
# backend/app/services/calendar/business_calendar_service.py
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging
from enum import Enum
import holidays
from calendar import monthrange

logger = logging.getLogger(__name__)

class HolidayType(Enum):
    """Types of holidays"""
    FEDERAL = "federal"
    COMPANY = "company"
    DEPARTMENT = "department"
    REGIONAL = "regional"
    FLOATING = "floating"
    OBSERVANCE = "observance"

class BusinessDayRule(Enum):
    """Business day calculation rules"""
    STRICT = "strict"  # Exactly business days only
    FLEXIBLE = "flexible"  # Allow next business day if weekend/holiday
    EXTENDED = "extended"  # Use extended business hours if needed

@dataclass
class Holiday:
    """Holiday definition"""
    holiday_id: str
    name: str
    date: date
    holiday_type: HolidayType
    description: str
    is_observed: bool = True
    affects_delivery: bool = True
    departments: List[str] = field(default_factory=list)
    regions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class BusinessHours:
    """Business hours configuration"""
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    is_business_day: bool = True
    extended_hours_start: Optional[str] = None
    extended_hours_end: Optional[str] = None

@dataclass
class WorkingDay:
    """Working day information"""
    date: date
    is_business_day: bool
    is_holiday: bool
    holiday_names: List[str]
    business_hours: Optional[BusinessHours]
    delivery_allowed: bool
    next_business_day: Optional[date]
    extended_hours_available: bool = False

class BusinessCalendarService:
    """
    Comprehensive Business Calendar Service
    Holiday management, business day calculation, and delivery scheduling
    """
    
    def __init__(self, db: Session, country: str = 'US', region: Optional[str] = None):
        self.db = db
        self.country = country
        self.region = region
        
        # Initialize holiday calendar
        self.federal_holidays = holidays.country_holidays(country)
        
        # Business hours configuration
        self.business_hours = self._load_business_hours()
        
        # Company holidays
        self.company_holidays = self._load_company_holidays()
        
        # Delivery rules
        self.delivery_rules = self._load_delivery_rules()
        
    def get_working_day_info(self, target_date: date) -> WorkingDay:
        """Get comprehensive working day information"""
        
        # Check if it's a weekend
        is_weekend = target_date.weekday() >= 5  # Saturday=5, Sunday=6
        
        # Check for holidays
        is_federal_holiday = target_date in self.federal_holidays
        company_holiday = self._get_company_holiday(target_date)
        is_company_holiday = company_holiday is not None
        
        # Collect holiday names
        holiday_names = []
        if is_federal_holiday:
            holiday_names.append(self.federal_holidays.get(target_date))
        if is_company_holiday:
            holiday_names.append(company_holiday.name)
        
        # Determine if it's a business day
        is_business_day = not (is_weekend or is_federal_holiday or is_company_holiday)
        
        # Get business hours for this day
        business_hours = self._get_business_hours(target_date.weekday())
        
        # Determine if delivery is allowed
        delivery_allowed = self._is_delivery_allowed(target_date, is_business_day, company_holiday)
        
        # Find next business day if needed
        next_business_day = None
        if not is_business_day:
            next_business_day = self.get_next_business_day(target_date)
        
        # Check for extended hours availability
        extended_hours_available = (business_hours and 
                                  business_hours.extended_hours_start and 
                                  business_hours.extended_hours_end)
        
        return WorkingDay(
            date=target_date,
            is_business_day=is_business_day,
            is_holiday=is_federal_holiday or is_company_holiday,
            holiday_names=holiday_names,
            business_hours=business_hours,
            delivery_allowed=delivery_allowed,
            next_business_day=next_business_day,
            extended_hours_available=extended_hours_available
        )
    
    def get_next_business_day(self, from_date: date, skip_days: int = 0) -> date:
        """Get the next business day after the given date"""
        
        current_date = from_date + timedelta(days=1)
        business_days_found = 0
        
        # Look ahead up to 30 days to find business days
        for _ in range(30):
            working_day = self.get_working_day_info(current_date)
            
            if working_day.is_business_day and working_day.delivery_allowed:
                if business_days_found >= skip_days:
                    return current_date
                business_days_found += 1
            
            current_date += timedelta(days=1)
        
        # Fallback: return a week from the original date
        return from_date + timedelta(days=7)
    
    def get_business_days_in_range(self, start_date: date, end_date: date) -> List[WorkingDay]:
        """Get all business days in a date range"""
        
        business_days = []
        current_date = start_date
        
        while current_date <= end_date:
            working_day = self.get_working_day_info(current_date)
            if working_day.is_business_day and working_day.delivery_allowed:
                business_days.append(working_day)
            
            current_date += timedelta(days=1)
        
        return business_days
    
    def calculate_business_days_between(self, start_date: date, end_date: date) -> int:
        """Calculate number of business days between two dates"""
        
        if start_date >= end_date:
            return 0
        
        business_days = self.get_business_days_in_range(start_date, end_date)
        return len(business_days)
    
    def add_business_days(self, from_date: date, business_days: int) -> date:
        """Add business days to a date"""
        
        if business_days <= 0:
            return from_date
        
        current_date = from_date
        days_added = 0
        
        while days_added < business_days:
            current_date += timedelta(days=1)
            working_day = self.get_working_day_info(current_date)
            
            if working_day.is_business_day and working_day.delivery_allowed:
                days_added += 1
        
        return current_date
    
    def get_optimal_delivery_time(self, 
                                 target_date: date,
                                 preferred_time: Optional[str] = None,
                                 rule: BusinessDayRule = BusinessDayRule.FLEXIBLE) -> Dict[str, Any]:
        """Get optimal delivery time considering business rules"""
        
        working_day = self.get_working_day_info(target_date)
        
        result = {
            'original_date': target_date,
            'recommended_date': target_date,
            'recommended_time': preferred_time or '08:00',
            'is_optimal': working_day.delivery_allowed,
            'adjustments_made': [],
            'business_day_info': working_day
        }
        
        # Apply business day rules
        if not working_day.delivery_allowed:
            if rule == BusinessDayRule.STRICT:
                result['is_optimal'] = False
                result['adjustments_made'].append('Delivery not allowed on specified date')
                
            elif rule == BusinessDayRule.FLEXIBLE:
                next_business_day = self.get_next_business_day(target_date)
                result['recommended_date'] = next_business_day
                result['adjustments_made'].append(f'Moved to next business day: {next_business_day}')
                result['is_optimal'] = True
                
            elif rule == BusinessDayRule.EXTENDED:
                if working_day.extended_hours_available:
                    result['recommended_time'] = working_day.business_hours.extended_hours_start
                    result['adjustments_made'].append('Using extended business hours')
                    result['is_optimal'] = True
                else:
                    # Fall back to flexible rule
                    next_business_day = self.get_next_business_day(target_date)
                    result['recommended_date'] = next_business_day
                    result['adjustments_made'].append(f'No extended hours available, moved to: {next_business_day}')
                    result['is_optimal'] = True
        
        # Optimize time within business hours
        if result['is_optimal'] and working_day.business_hours:
            optimized_time = self._optimize_delivery_time(
                result['recommended_time'],
                working_day.business_hours
            )
            
            if optimized_time != result['recommended_time']:
                result['recommended_time'] = optimized_time
                result['adjustments_made'].append(f'Optimized delivery time to: {optimized_time}')
        
        return result
    
    def create_holiday(self, holiday: Holiday) -> bool:
        """Create a new company holiday"""
        
        try:
            # Store holiday in database
            insert_query = """
                INSERT INTO company_holidays 
                (holiday_id, name, date, holiday_type, description, is_observed, 
                 affects_delivery, departments, regions, created_at)
                VALUES (:holiday_id, :name, :date, :holiday_type, :description, 
                        :is_observed, :affects_delivery, :departments, :regions, :created_at)
            """
            
            self.db.execute(text(insert_query), {
                'holiday_id': holiday.holiday_id,
                'name': holiday.name,
                'date': holiday.date,
                'holiday_type': holiday.holiday_type.value,
                'description': holiday.description,
                'is_observed': holiday.is_observed,
                'affects_delivery': holiday.affects_delivery,
                'departments': json.dumps(holiday.departments),
                'regions': json.dumps(holiday.regions),
                'created_at': holiday.created_at
            })
            
            self.db.commit()
            
            # Reload company holidays
            self.company_holidays = self._load_company_holidays()
            
            logger.info(f"Created holiday: {holiday.name} on {holiday.date}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create holiday: {str(e)}")
            self.db.rollback()
            return False
    
    def get_holidays_in_range(self, start_date: date, end_date: date) -> List[Holiday]:
        """Get all holidays in a date range"""
        
        holidays_in_range = []
        
        # Add federal holidays
        for holiday_date in self.federal_holidays:
            if start_date <= holiday_date <= end_date:
                holidays_in_range.append(Holiday(
                    holiday_id=f"federal_{holiday_date}",
                    name=self.federal_holidays[holiday_date],
                    date=holiday_date,
                    holiday_type=HolidayType.FEDERAL,
                    description=f"Federal holiday: {self.federal_holidays[holiday_date]}"
                ))
        
        # Add company holidays
        for holiday in self.company_holidays:
            if start_date <= holiday.date <= end_date:
                holidays_in_range.append(holiday)
        
        # Sort by date
        holidays_in_range.sort(key=lambda h: h.date)
        
        return holidays_in_range
    
    def _load_business_hours(self) -> List[BusinessHours]:
        """Load business hours configuration"""
        
        # Default business hours (Monday-Friday, 8 AM - 6 PM)
        default_hours = [
            BusinessHours(0, '08:00', '18:00', True, '07:00', '20:00'),  # Monday
            BusinessHours(1, '08:00', '18:00', True, '07:00', '20:00'),  # Tuesday
            BusinessHours(2, '08:00', '18:00', True, '07:00', '20:00'),  # Wednesday
            BusinessHours(3, '08:00', '18:00', True, '07:00', '20:00'),  # Thursday
            BusinessHours(4, '08:00', '18:00', True, '07:00', '20:00'),  # Friday
            BusinessHours(5, '10:00', '14:00', False),  # Saturday (limited)
            BusinessHours(6, '00:00', '00:00', False)   # Sunday (closed)
        ]
        
        try:
            # Load from database if available
            query = """
                SELECT day_of_week, start_time, end_time, is_business_day,
                       extended_hours_start, extended_hours_end
                FROM business_hours_config
                ORDER BY day_of_week
            """
            
            result = self.db.execute(text(query))
            hours_config = []
            
            for row in result.fetchall():
                hours_config.append(BusinessHours(
                    day_of_week=row.day_of_week,
                    start_time=row.start_time,
                    end_time=row.end_time,
                    is_business_day=row.is_business_day,
                    extended_hours_start=row.extended_hours_start,
                    extended_hours_end=row.extended_hours_end
                ))
            
            return hours_config if hours_config else default_hours
            
        except Exception as e:
            logger.warning(f"Could not load business hours from database: {str(e)}")
            return default_hours
    
    def _load_company_holidays(self) -> List[Holiday]:
        """Load company holidays from database"""
        
        try:
            query = """
                SELECT holiday_id, name, date, holiday_type, description,
                       is_observed, affects_delivery, departments, regions, created_at
                FROM company_holidays
                WHERE is_observed = true
                ORDER BY date
            """
            
            result = self.db.execute(text(query))
            holidays = []
            
            for row in result.fetchall():
                departments = json.loads(row.departments) if row.departments else []
                regions = json.loads(row.regions) if row.regions else []
                
                holidays.append(Holiday(
                    holiday_id=row.holiday_id,
                    name=row.name,
                    date=row.date,
                    holiday_type=HolidayType(row.holiday_type),
                    description=row.description,
                    is_observed=row.is_observed,
                    affects_delivery=row.affects_delivery,
                    departments=departments,
                    regions=regions,
                    created_at=row.created_at
                ))
            
            return holidays
            
        except Exception as e:
            logger.warning(f"Could not load company holidays: {str(e)}")
            return []
    
    def _load_delivery_rules(self) -> Dict[str, Any]:
        """Load delivery rules configuration"""
        
        return {
            'allow_weekend_delivery': False,
            'allow_holiday_delivery': False,
            'emergency_override_allowed': True,
            'extended_hours_threshold': 'high_priority',
            'business_day_rule': BusinessDayRule.FLEXIBLE,
            'max_delivery_window_days': 14
        }
    
    def _get_company_holiday(self, target_date: date) -> Optional[Holiday]:
        """Get company holiday for a specific date"""
        
        for holiday in self.company_holidays:
            if holiday.date == target_date and holiday.affects_delivery:
                return holiday
        return None
    
    def _get_business_hours(self, day_of_week: int) -> Optional[BusinessHours]:
        """Get business hours for a specific day of week"""
        
        for hours in self.business_hours:
            if hours.day_of_week == day_of_week:
                return hours
        return None
    
    def _is_delivery_allowed(self, 
                           target_date: date, 
                           is_business_day: bool, 
                           company_holiday: Optional[Holiday]) -> bool:
        """Determine if delivery is allowed on a specific date"""
        
        # Check business day rules
        if not is_business_day:
            if target_date.weekday() >= 5:  # Weekend
                return self.delivery_rules.get('allow_weekend_delivery', False)
            elif company_holiday:
                return (not company_holiday.affects_delivery or 
                       self.delivery_rules.get('allow_holiday_delivery', False))
            else:
                return self.delivery_rules.get('allow_holiday_delivery', False)
        
        return True
    
    def _optimize_delivery_time(self, 
                              preferred_time: str, 
                              business_hours: BusinessHours) -> str:
        """Optimize delivery time within business hours"""
        
        if not business_hours.is_business_day:
            return preferred_time
        
        # Parse times
        try:
            from datetime import time
            preferred = time.fromisoformat(preferred_time)
            start = time.fromisoformat(business_hours.start_time)
            end = time.fromisoformat(business_hours.end_time)
            
            # Ensure time is within business hours
            if preferred < start:
                return business_hours.start_time
            elif preferred > end:
                return business_hours.end_time
            else:
                return preferred_time
                
        except Exception:
            # Fallback to business hours start time
            return business_hours.start_time

# Factory function
def create_business_calendar_service(db: Session, country: str = 'US') -> BusinessCalendarService:
    """Create and configure business calendar service"""
    return BusinessCalendarService(db=db, country=country)
```

This is the foundation of our Business Calendar System. Should I continue with:

1. **Complete the Advanced Conditional Logic Engine** for complex delivery rules
2. **Build the Multi-level Escalation Workflows** system
3. **Create the Dynamic Recipient Management** service
4. **Move to the Predictive Analytics** component

What would you like me to focus on next for Day 6?