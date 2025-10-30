# Business Calendar API Endpoints - Phase B Sprint 2 Day 6
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.calendar.business_calendar_service import (
    BusinessCalendarService,
    Holiday,
    HolidayType,
    BusinessDayRule,
    create_business_calendar_service
)

router = APIRouter()

# Pydantic Models
class HolidayCreate(BaseModel):
    """Schema for creating a new holiday"""
    holiday_id: str = Field(..., description="Unique identifier for the holiday")
    name: str = Field(..., description="Holiday name")
    date: date = Field(..., description="Holiday date")
    holiday_type: HolidayType = Field(default=HolidayType.COMPANY, description="Type of holiday")
    description: str = Field(..., description="Holiday description")
    is_observed: bool = Field(default=True, description="Whether the holiday is observed")
    affects_delivery: bool = Field(default=True, description="Whether the holiday affects delivery")
    departments: List[str] = Field(default=[], description="Affected departments")
    regions: List[str] = Field(default=[], description="Affected regions")

class HolidayResponse(BaseModel):
    """Schema for holiday response"""
    holiday_id: str
    name: str
    date: date
    holiday_type: str
    description: str
    is_observed: bool
    affects_delivery: bool
    departments: List[str]
    regions: List[str]
    created_at: datetime

class WorkingDayResponse(BaseModel):
    """Schema for working day information"""
    date: date
    is_business_day: bool
    is_holiday: bool
    holiday_names: List[str]
    delivery_allowed: bool
    next_business_day: Optional[date]
    extended_hours_available: bool

class OptimalDeliveryResponse(BaseModel):
    """Schema for optimal delivery time response"""
    original_date: date
    recommended_date: date
    recommended_time: str
    is_optimal: bool
    adjustments_made: List[str]

class CalendarSummaryResponse(BaseModel):
    """Schema for calendar summary response"""
    month: int
    year: int
    total_days: int
    business_days: int
    holidays: int
    weekends: int
    delivery_days_available: int
    holidays_list: List[Dict[str, Any]]
    business_days_list: List[Dict[str, Any]]

class CapacityForecastResponse(BaseModel):
    """Schema for delivery capacity forecast"""
    forecast_period: Dict[str, Any]
    capacity_summary: Dict[str, Any]
    upcoming_holidays: List[Dict[str, Any]]
    weekly_breakdown: Dict[str, Any]
    recommendations: List[str]

@router.get("/working-day/{target_date}", response_model=WorkingDayResponse)
async def get_working_day_info(
    target_date: date,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive working day information for a specific date
    
    Returns business day status, holiday information, and delivery availability
    """
    try:
        calendar_service = create_business_calendar_service(db)
        working_day = calendar_service.get_working_day_info(target_date)
        
        return WorkingDayResponse(
            date=working_day.date,
            is_business_day=working_day.is_business_day,
            is_holiday=working_day.is_holiday,
            holiday_names=working_day.holiday_names,
            delivery_allowed=working_day.delivery_allowed,
            next_business_day=working_day.next_business_day,
            extended_hours_available=working_day.extended_hours_available
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get working day info: {str(e)}")

@router.get("/next-business-day/{from_date}")
async def get_next_business_day(
    from_date: date,
    skip_days: int = Query(default=0, description="Number of business days to skip"),
    db: Session = Depends(get_db)
):
    """
    Get the next business day after the specified date
    
    Optionally skip a number of business days
    """
    try:
        calendar_service = create_business_calendar_service(db)
        next_business_day = calendar_service.get_next_business_day(from_date, skip_days)
        
        return {
            "from_date": from_date,
            "skip_days": skip_days,
            "next_business_day": next_business_day
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next business day: {str(e)}")

@router.get("/business-days/range")
async def get_business_days_in_range(
    start_date: date = Query(..., description="Range start date"),
    end_date: date = Query(..., description="Range end date"),
    db: Session = Depends(get_db)
):
    """
    Get all business days in a specified date range
    """
    try:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        calendar_service = create_business_calendar_service(db)
        business_days = calendar_service.get_business_days_in_range(start_date, end_date)
        
        return {
            "range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "business_days_count": len(business_days),
            "business_days": [
                {
                    "date": bd.date,
                    "is_business_day": bd.is_business_day,
                    "delivery_allowed": bd.delivery_allowed,
                    "holiday_names": bd.holiday_names
                } for bd in business_days
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get business days in range: {str(e)}")

@router.get("/business-days/count")
async def calculate_business_days_between(
    start_date: date = Query(..., description="Range start date"),
    end_date: date = Query(..., description="Range end date"),
    db: Session = Depends(get_db)
):
    """
    Calculate the number of business days between two dates
    """
    try:
        calendar_service = create_business_calendar_service(db)
        business_days_count = calendar_service.calculate_business_days_between(start_date, end_date)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "business_days_count": business_days_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate business days: {str(e)}")

@router.get("/business-days/add")
async def add_business_days(
    from_date: date = Query(..., description="Starting date"),
    business_days: int = Query(..., description="Number of business days to add"),
    db: Session = Depends(get_db)
):
    """
    Add a specified number of business days to a date
    """
    try:
        if business_days < 0:
            raise HTTPException(status_code=400, detail="Business days must be non-negative")
        
        calendar_service = create_business_calendar_service(db)
        result_date = calendar_service.add_business_days(from_date, business_days)
        
        return {
            "from_date": from_date,
            "business_days_added": business_days,
            "result_date": result_date
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add business days: {str(e)}")

@router.get("/optimal-delivery-time", response_model=OptimalDeliveryResponse)
async def get_optimal_delivery_time(
    target_date: date = Query(..., description="Target delivery date"),
    preferred_time: Optional[str] = Query(default=None, description="Preferred delivery time (HH:MM)"),
    rule: BusinessDayRule = Query(default=BusinessDayRule.FLEXIBLE, description="Business day rule"),
    db: Session = Depends(get_db)
):
    """
    Get optimal delivery time considering business rules and constraints
    """
    try:
        calendar_service = create_business_calendar_service(db)
        optimal_delivery = calendar_service.get_optimal_delivery_time(
            target_date, preferred_time, rule
        )
        
        return OptimalDeliveryResponse(
            original_date=optimal_delivery['original_date'],
            recommended_date=optimal_delivery['recommended_date'],
            recommended_time=optimal_delivery['recommended_time'],
            is_optimal=optimal_delivery['is_optimal'],
            adjustments_made=optimal_delivery['adjustments_made']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimal delivery time: {str(e)}")

@router.post("/holidays", response_model=Dict[str, Any])
async def create_holiday(
    holiday: HolidayCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new company holiday
    """
    try:
        calendar_service = create_business_calendar_service(db)
        
        # Convert Pydantic model to Holiday dataclass
        holiday_obj = Holiday(
            holiday_id=holiday.holiday_id,
            name=holiday.name,
            date=holiday.date,
            holiday_type=holiday.holiday_type,
            description=holiday.description,
            is_observed=holiday.is_observed,
            affects_delivery=holiday.affects_delivery,
            departments=holiday.departments,
            regions=holiday.regions
        )
        
        success = calendar_service.create_holiday(holiday_obj)
        
        if success:
            return {
                "success": True,
                "message": f"Holiday '{holiday.name}' created successfully",
                "holiday_id": holiday.holiday_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create holiday")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create holiday: {str(e)}")

@router.get("/holidays/range", response_model=List[HolidayResponse])
async def get_holidays_in_range(
    start_date: date = Query(..., description="Range start date"),
    end_date: date = Query(..., description="Range end date"),
    db: Session = Depends(get_db)
):
    """
    Get all holidays in a specified date range
    """
    try:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        calendar_service = create_business_calendar_service(db)
        holidays = calendar_service.get_holidays_in_range(start_date, end_date)
        
        return [
            HolidayResponse(
                holiday_id=h.holiday_id,
                name=h.name,
                date=h.date,
                holiday_type=h.holiday_type.value,
                description=h.description,
                is_observed=h.is_observed,
                affects_delivery=h.affects_delivery,
                departments=h.departments,
                regions=h.regions,
                created_at=h.created_at
            ) for h in holidays
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get holidays in range: {str(e)}")

@router.get("/calendar-summary/{year}/{month}", response_model=CalendarSummaryResponse)
async def get_calendar_summary(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive calendar summary for a specific month
    """
    try:
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        calendar_service = create_business_calendar_service(db)
        summary = calendar_service.get_calendar_summary(month, year)
        
        return CalendarSummaryResponse(**summary)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get calendar summary: {str(e)}")

@router.get("/capacity-forecast", response_model=CapacityForecastResponse)
async def get_delivery_capacity_forecast(
    days_ahead: int = Query(default=30, description="Number of days to forecast ahead"),
    db: Session = Depends(get_db)
):
    """
    Get delivery capacity forecast for upcoming days
    """
    try:
        if days_ahead < 1 or days_ahead > 365:
            raise HTTPException(status_code=400, detail="Days ahead must be between 1 and 365")
        
        calendar_service = create_business_calendar_service(db)
        forecast = calendar_service.get_delivery_capacity_forecast(days_ahead)
        
        return CapacityForecastResponse(**forecast)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get capacity forecast: {str(e)}")

@router.get("/health")
async def calendar_service_health(db: Session = Depends(get_db)):
    """
    Health check endpoint for the business calendar service
    """
    try:
        calendar_service = create_business_calendar_service(db)
        
        # Test basic functionality
        today = date.today()
        working_day = calendar_service.get_working_day_info(today)
        next_business_day = calendar_service.get_next_business_day(today)
        
        return {
            "status": "healthy",
            "service": "Business Calendar Service",
            "timestamp": datetime.now(),
            "test_results": {
                "today_is_business_day": working_day.is_business_day,
                "next_business_day": next_business_day,
                "holidays_loaded": len(calendar_service.company_holidays),
                "business_hours_configured": len(calendar_service.business_hours)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")