# Business Calendar Service Tests - Phase B Sprint 2 Day 6
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.calendar.business_calendar_service import (
    BusinessCalendarService,
    Holiday,
    HolidayType,
    BusinessDayRule,
    BusinessHours,
    WorkingDay,
    create_business_calendar_service
)

class TestBusinessCalendarService:
    """Test suite for Business Calendar Service"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def calendar_service(self, mock_db):
        """Create calendar service with mocked dependencies"""
        with patch('app.services.calendar.business_calendar_service.holidays.country_holidays') as mock_holidays:
            # Mock federal holidays
            mock_holidays.return_value = {
                date(2024, 1, 1): "New Year's Day",
                date(2024, 7, 4): "Independence Day",
                date(2024, 12, 25): "Christmas Day"
            }
            
            service = BusinessCalendarService(mock_db, country='US')
            
            # Mock database queries
            mock_db.execute.return_value.scalar.return_value = False  # No tables exist
            mock_db.execute.return_value.fetchall.return_value = []   # No data
            
            return service
    
    def test_get_working_day_info_business_day(self, calendar_service):
        """Test working day info for a regular business day"""
        # Test a Tuesday (business day)
        test_date = date(2024, 1, 2)  # Tuesday
        
        working_day = calendar_service.get_working_day_info(test_date)
        
        assert working_day.date == test_date
        assert working_day.is_business_day == True
        assert working_day.is_holiday == False
        assert working_day.delivery_allowed == True
        assert len(working_day.holiday_names) == 0
    
    def test_get_working_day_info_weekend(self, calendar_service):
        """Test working day info for a weekend"""
        # Test a Saturday
        test_date = date(2024, 1, 6)  # Saturday
        
        working_day = calendar_service.get_working_day_info(test_date)
        
        assert working_day.date == test_date
        assert working_day.is_business_day == False
        assert working_day.delivery_allowed == False
        assert working_day.next_business_day is not None
    
    def test_get_working_day_info_federal_holiday(self, calendar_service):
        """Test working day info for a federal holiday"""
        # Test New Year's Day
        test_date = date(2024, 1, 1)  # Monday, New Year's Day
        
        working_day = calendar_service.get_working_day_info(test_date)
        
        assert working_day.date == test_date
        assert working_day.is_business_day == False
        assert working_day.is_holiday == True
        assert "New Year's Day" in working_day.holiday_names
        assert working_day.delivery_allowed == False
    
    def test_get_next_business_day(self, calendar_service):
        """Test getting next business day"""
        # Start from Friday, should get Monday
        friday = date(2024, 1, 5)  # Friday
        
        next_business_day = calendar_service.get_next_business_day(friday)
        
        # Should be Monday (skipping weekend)
        expected_monday = date(2024, 1, 8)
        assert next_business_day == expected_monday
    
    def test_get_next_business_day_with_skip(self, calendar_service):
        """Test getting next business day with skip days"""
        # Start from Monday, skip 2 business days, should get Thursday
        monday = date(2024, 1, 8)  # Monday
        
        next_business_day = calendar_service.get_next_business_day(monday, skip_days=2)
        
        # Should be Thursday
        expected_thursday = date(2024, 1, 11)
        assert next_business_day == expected_thursday
    
    def test_get_business_days_in_range(self, calendar_service):
        """Test getting business days in a range"""
        # Test a week: Monday to Sunday
        start_date = date(2024, 1, 8)   # Monday
        end_date = date(2024, 1, 14)    # Sunday
        
        business_days = calendar_service.get_business_days_in_range(start_date, end_date)
        
        # Should have 5 business days (Mon-Fri)
        assert len(business_days) == 5
        
        # Check that all returned days are business days
        for bd in business_days:
            assert bd.is_business_day == True
            assert bd.delivery_allowed == True
    
    def test_calculate_business_days_between(self, calendar_service):
        """Test calculating business days between dates"""
        # Test from Monday to Friday (same week)
        start_date = date(2024, 1, 8)   # Monday
        end_date = date(2024, 1, 12)    # Friday
        
        count = calendar_service.calculate_business_days_between(start_date, end_date)
        
        # Should be 4 business days (Tue, Wed, Thu, Fri)
        assert count == 4
    
    def test_add_business_days(self, calendar_service):
        """Test adding business days to a date"""
        # Start from Monday, add 5 business days
        monday = date(2024, 1, 8)  # Monday
        
        result_date = calendar_service.add_business_days(monday, 5)
        
        # Should be next Monday (Mon + 5 business days = next Mon)
        expected_date = date(2024, 1, 15)  # Next Monday
        assert result_date == expected_date
    
    def test_get_optimal_delivery_time_flexible_rule(self, calendar_service):
        """Test optimal delivery time with flexible rule"""
        # Test delivery on a Saturday (weekend)
        saturday = date(2024, 1, 6)  # Saturday
        
        result = calendar_service.get_optimal_delivery_time(
            saturday, 
            preferred_time="09:00",
            rule=BusinessDayRule.FLEXIBLE
        )
        
        assert result['original_date'] == saturday
        assert result['recommended_date'] != saturday  # Should be moved
        assert result['is_optimal'] == True
        assert len(result['adjustments_made']) > 0
        assert 'Moved to next business day' in result['adjustments_made'][0]
    
    def test_get_optimal_delivery_time_strict_rule(self, calendar_service):
        """Test optimal delivery time with strict rule"""
        # Test delivery on a Saturday (weekend)
        saturday = date(2024, 1, 6)  # Saturday
        
        result = calendar_service.get_optimal_delivery_time(
            saturday,
            preferred_time="09:00", 
            rule=BusinessDayRule.STRICT
        )
        
        assert result['original_date'] == saturday
        assert result['is_optimal'] == False
        assert 'Delivery not allowed' in result['adjustments_made'][0]
    
    def test_create_holiday(self, calendar_service):
        """Test creating a new holiday"""
        holiday = Holiday(
            holiday_id="test_holiday_2024",
            name="Test Holiday",
            date=date(2024, 6, 15),
            holiday_type=HolidayType.COMPANY,
            description="Test company holiday"
        )
        
        # Mock successful database operation
        calendar_service.db.execute.return_value = None
        calendar_service.db.commit.return_value = None
        
        result = calendar_service.create_holiday(holiday)
        
        assert result == True
        calendar_service.db.execute.assert_called()
        calendar_service.db.commit.assert_called()
    
    def test_get_holidays_in_range(self, calendar_service):
        """Test getting holidays in a date range"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        holidays = calendar_service.get_holidays_in_range(start_date, end_date)
        
        # Should include federal holidays
        holiday_names = [h.name for h in holidays]
        assert "New Year's Day" in holiday_names
        assert "Independence Day" in holiday_names
        assert "Christmas Day" in holiday_names
    
    def test_get_calendar_summary(self, calendar_service):
        """Test getting calendar summary for a month"""
        summary = calendar_service.get_calendar_summary(1, 2024)  # January 2024
        
        assert summary['month'] == 1
        assert summary['year'] == 2024
        assert summary['total_days'] == 31
        assert summary['business_days'] >= 0
        assert summary['holidays'] >= 0
        assert summary['weekends'] >= 0
        assert 'holidays_list' in summary
        assert 'business_days_list' in summary
    
    def test_get_delivery_capacity_forecast(self, calendar_service):
        """Test getting delivery capacity forecast"""
        forecast = calendar_service.get_delivery_capacity_forecast(30)
        
        assert 'forecast_period' in forecast
        assert 'capacity_summary' in forecast
        assert 'upcoming_holidays' in forecast
        assert 'weekly_breakdown' in forecast
        assert 'recommendations' in forecast
        
        # Validate forecast period
        assert forecast['forecast_period']['total_days'] == 30
        
        # Validate capacity summary
        capacity = forecast['capacity_summary']
        assert 'total_business_days' in capacity
        assert 'total_delivery_capacity' in capacity
        assert capacity['average_daily_capacity'] == 8
    
    def test_business_hours_optimization(self, calendar_service):
        """Test business hours time optimization"""
        # Test time before business hours
        result = calendar_service._optimize_delivery_time(
            "06:00",
            BusinessHours(0, '08:00', '18:00', True)
        )
        assert result == "08:00"
        
        # Test time after business hours
        result = calendar_service._optimize_delivery_time(
            "20:00",
            BusinessHours(0, '08:00', '18:00', True)
        )
        assert result == "18:00"
        
        # Test time within business hours
        result = calendar_service._optimize_delivery_time(
            "10:00",
            BusinessHours(0, '08:00', '18:00', True)
        )
        assert result == "10:00"
    
    def test_factory_function(self, mock_db):
        """Test the factory function"""
        with patch('app.services.calendar.business_calendar_service.holidays.country_holidays'):
            service = create_business_calendar_service(mock_db, country='US')
            
            assert isinstance(service, BusinessCalendarService)
            assert service.db == mock_db
            assert service.country == 'US'


class TestBusinessCalendarIntegration:
    """Integration tests for Business Calendar Service"""
    
    @pytest.mark.integration
    def test_real_federal_holidays(self):
        """Test with real federal holidays library"""
        import holidays
        
        us_holidays = holidays.country_holidays('US')
        
        # Check that common holidays exist
        assert date(2024, 1, 1) in us_holidays  # New Year's Day
        assert date(2024, 7, 4) in us_holidays  # Independence Day
        assert date(2024, 12, 25) in us_holidays  # Christmas Day
    
    @pytest.mark.integration
    def test_business_day_calculations_across_year(self):
        """Test business day calculations across different scenarios"""
        mock_db = Mock(spec=Session)
        mock_db.execute.return_value.scalar.return_value = False
        mock_db.execute.return_value.fetchall.return_value = []
        
        service = BusinessCalendarService(mock_db, country='US')
        
        # Test various scenarios
        test_cases = [
            # (start_date, expected_next_business_day_weekday)
            (date(2024, 1, 5), 0),   # Friday -> Monday (weekday 0)
            (date(2024, 1, 6), 0),   # Saturday -> Monday
            (date(2024, 1, 7), 0),   # Sunday -> Monday
            (date(2024, 1, 1), 1),   # Holiday Monday -> Tuesday (weekday 1)
        ]
        
        for start_date, expected_weekday in test_cases:
            next_bd = service.get_next_business_day(start_date)
            assert next_bd.weekday() == expected_weekday
    
    @pytest.mark.integration 
    def test_month_boundary_calculations(self):
        """Test calculations that cross month boundaries"""
        mock_db = Mock(spec=Session)
        mock_db.execute.return_value.scalar.return_value = False
        mock_db.execute.return_value.fetchall.return_value = []
        
        service = BusinessCalendarService(mock_db, country='US')
        
        # Test end of month to beginning of next month
        end_of_jan = date(2024, 1, 31)  # Wednesday
        result = service.add_business_days(end_of_jan, 3)
        
        # Should be in February
        assert result.month == 2
        assert result.year == 2024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])