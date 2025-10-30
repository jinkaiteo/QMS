# QMS Department Analytics Service - Phase A Sprint 2
# Service layer for department analytics and organizational metrics

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from fastapi import HTTPException
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from app.models.user import User
from app.models.organization_management.department_hierarchy import Department, DepartmentRole, Organization
from app.models.user_management.user_profile import UserSession
from app.schemas.organization_management.department_hierarchy import (
    DepartmentAnalytics, OrganizationAnalytics
)
from app.core.exceptions import AuthorizationException


class DepartmentAnalyticsService:
    """Service for department and organizational analytics"""
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    def get_department_metrics(self, department_id: int, include_children: bool = True) -> DepartmentAnalytics:
        """Get comprehensive department metrics and analytics"""
        if not self.current_user.has_permission("analytics.view", "core"):
            raise AuthorizationException("Insufficient permissions to view analytics")
        
        department = self.db.query(Department).filter(
            Department.id == department_id,
            Department.is_active == True
        ).first()
        
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Get user counts
        direct_users = len(department.users)
        
        if include_children:
            total_users = self._get_total_users_in_hierarchy(department)
        else:
            total_users = direct_users
        
        # Get role distribution for this department
        role_distribution = self._get_department_role_distribution(department_id)
        
        # Get activity metrics
        activity_metrics = self._get_department_activity_metrics(department_id, include_children)
        
        # Get most/least active users
        most_active_users = self._get_most_active_users(department_id, limit=5)
        least_active_users = self._get_least_active_users(department_id, limit=5)
        
        # Get training completion rate (placeholder - would integrate with TMS)
        training_completion_rate = self._get_training_completion_rate(department_id)
        
        # Get quality events count (placeholder - would integrate with QRM)
        quality_events_count = self._get_quality_events_count(department_id)
        
        return DepartmentAnalytics(
            department_id=department_id,
            department_name=department.name,
            hierarchy_level=department.hierarchy_level,
            direct_users=direct_users,
            total_users=total_users,
            child_departments=len(department.child_departments),
            role_distribution=role_distribution,
            recent_logins_30d=activity_metrics["recent_logins"],
            average_session_duration_minutes=activity_metrics["avg_session_duration"],
            department_head={
                "id": department.department_head.id,
                "full_name": department.department_head.full_name,
                "job_title": department.department_head.job_title,
                "profile_picture_url": department.department_head.profile_picture_url
            } if department.department_head else None,
            cost_center=department.cost_center,
            location=department.location,
            department_type=department.department_type,
            most_active_users=most_active_users,
            least_active_users=least_active_users,
            training_completion_rate=training_completion_rate,
            quality_events_count=quality_events_count
        )
    
    def get_organization_hierarchy_analytics(self, organization_id: int) -> OrganizationAnalytics:
        """Get organization-wide hierarchy analytics"""
        if not self.current_user.has_permission("analytics.view", "core"):
            raise AuthorizationException("Insufficient permissions to view analytics")
        
        organization = self.db.query(Organization).filter(
            Organization.id == organization_id,
            Organization.is_active == True
        ).first()
        
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Get all departments in organization
        departments = self.db.query(Department).filter(
            Department.organization_id == organization_id,
            Department.is_active == True
        ).all()
        
        # Calculate hierarchy statistics
        max_depth = max([dept.hierarchy_level for dept in departments]) if departments else 0
        total_departments = len(departments)
        
        # Department type distribution
        type_distribution = {}
        for dept in departments:
            dept_type = dept.department_type or 'unspecified'
            type_distribution[dept_type] = type_distribution.get(dept_type, 0) + 1
        
        # User distribution by hierarchy level
        level_distribution = {}
        for dept in departments:
            level = f"Level_{dept.hierarchy_level}"
            user_count = len(dept.users)
            level_distribution[level] = level_distribution.get(level, 0) + user_count
        
        # Location distribution
        location_distribution = {}
        for dept in departments:
            location = dept.location or 'unspecified'
            location_distribution[location] = location_distribution.get(location, 0) + 1
        
        # Get active users in last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        active_users_30d = self.db.query(func.count(func.distinct(UserSession.user_id))).join(User).filter(
            User.organization_id == organization_id,
            UserSession.started_at >= cutoff_date
        ).scalar() or 0
        
        # Get departments without heads
        departments_without_heads = sum(1 for dept in departments if dept.department_head_id is None)
        
        # Get departments by type with details
        departments_by_type = {}
        for dept in departments:
            dept_type = dept.department_type or 'unspecified'
            if dept_type not in departments_by_type:
                departments_by_type[dept_type] = []
            
            departments_by_type[dept_type].append({
                "id": dept.id,
                "name": dept.name,
                "code": dept.code,
                "user_count": len(dept.users),
                "hierarchy_level": dept.hierarchy_level,
                "location": dept.location
            })
        
        # Calculate average training completion rate across organization
        avg_training_completion = self._get_organization_training_completion_rate(organization_id)
        
        # Get total quality events across organization
        total_quality_events = self._get_organization_quality_events_count(organization_id)
        
        # Get total active sessions
        total_active_sessions = self.db.query(func.count(UserSession.id)).join(User).filter(
            User.organization_id == organization_id,
            UserSession.is_active == True
        ).scalar() or 0
        
        return OrganizationAnalytics(
            organization_id=organization_id,
            organization_name=organization.name,
            total_departments=total_departments,
            max_hierarchy_depth=max_depth,
            department_type_distribution=type_distribution,
            user_distribution_by_level=level_distribution,
            total_users=sum(len(dept.users) for dept in departments),
            active_users_30d=active_users_30d,
            average_training_completion_rate=avg_training_completion,
            total_quality_events=total_quality_events,
            total_active_sessions=total_active_sessions,
            departments_without_heads=departments_without_heads,
            location_distribution=location_distribution,
            regulatory_region=organization.regulatory_region,
            departments_by_type=departments_by_type
        )
    
    def get_department_performance_comparison(self, organization_id: int) -> Dict[str, Any]:
        """Compare performance metrics across departments in organization"""
        if not self.current_user.has_permission("analytics.view", "core"):
            raise AuthorizationException("Insufficient permissions to view analytics")
        
        departments = self.db.query(Department).filter(
            Department.organization_id == organization_id,
            Department.is_active == True
        ).all()
        
        performance_data = []
        
        for dept in departments:
            # Get activity metrics
            activity_metrics = self._get_department_activity_metrics(dept.id, include_children=False)
            
            # Calculate productivity score (example algorithm)
            productivity_score = self._calculate_department_productivity_score(dept)
            
            performance_data.append({
                "department_id": dept.id,
                "department_name": dept.name,
                "department_type": dept.department_type,
                "hierarchy_level": dept.hierarchy_level,
                "user_count": len(dept.users),
                "recent_logins_30d": activity_metrics["recent_logins"],
                "avg_session_duration": activity_metrics["avg_session_duration"],
                "productivity_score": productivity_score,
                "training_completion_rate": self._get_training_completion_rate(dept.id),
                "quality_events_count": self._get_quality_events_count(dept.id)
            })
        
        # Sort by productivity score
        performance_data.sort(key=lambda x: x["productivity_score"], reverse=True)
        
        # Calculate organization averages
        org_averages = {
            "avg_productivity_score": sum(d["productivity_score"] for d in performance_data) / len(performance_data) if performance_data else 0,
            "avg_training_completion": sum(d["training_completion_rate"] or 0 for d in performance_data) / len(performance_data) if performance_data else 0,
            "avg_session_duration": sum(d["avg_session_duration"] or 0 for d in performance_data) / len(performance_data) if performance_data else 0
        }
        
        return {
            "organization_id": organization_id,
            "department_performance": performance_data,
            "organization_averages": org_averages,
            "top_performing_departments": performance_data[:5],
            "departments_needing_attention": [d for d in performance_data if d["productivity_score"] < org_averages["avg_productivity_score"] * 0.8]
        }
    
    def get_department_trends(self, department_id: int, days: int = 90) -> Dict[str, Any]:
        """Get department trends over specified time period"""
        if not self.current_user.has_permission("analytics.view", "core"):
            raise AuthorizationException("Insufficient permissions to view analytics")
        
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily login trends
        daily_logins = self._get_daily_login_trends(department_id, start_date, end_date)
        
        # Get weekly activity summaries
        weekly_activity = self._get_weekly_activity_trends(department_id, start_date, end_date)
        
        # Get user growth trends
        user_growth = self._get_user_growth_trends(department_id, start_date, end_date)
        
        return {
            "department_id": department_id,
            "department_name": department.name,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_login_trends": daily_logins,
            "weekly_activity_trends": weekly_activity,
            "user_growth_trends": user_growth,
            "trend_summary": {
                "avg_daily_logins": sum(daily_logins.values()) / len(daily_logins) if daily_logins else 0,
                "peak_activity_day": max(daily_logins, key=daily_logins.get) if daily_logins else None,
                "total_new_users": user_growth[-1]["total_users"] - user_growth[0]["total_users"] if len(user_growth) >= 2 else 0
            }
        }
    
    # Helper Methods
    def _get_total_users_in_hierarchy(self, department: Department) -> int:
        """Get total users in department and all child departments"""
        total = len(department.users)
        for child in department.child_departments:
            total += self._get_total_users_in_hierarchy(child)
        return total
    
    def _get_department_role_distribution(self, department_id: int) -> Dict[str, int]:
        """Get role distribution for department"""
        role_counts = self.db.query(
            func.count(DepartmentRole.id).label('count'),
            Role.display_name.label('role_name')
        ).join(Role).filter(
            DepartmentRole.department_id == department_id,
            DepartmentRole.is_active == True
        ).group_by(Role.display_name).all()
        
        return {role_name: count for count, role_name in role_counts}
    
    def _get_department_activity_metrics(self, department_id: int, include_children: bool) -> Dict[str, Any]:
        """Get activity metrics for department"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Get users in department (and children if requested)
        if include_children:
            dept = self.db.query(Department).filter(Department.id == department_id).first()
            all_dept_ids = [department_id] + [child.id for child in dept.get_all_descendants()]
            users_in_scope = self.db.query(User).filter(User.department_id.in_(all_dept_ids)).all()
        else:
            users_in_scope = self.db.query(User).filter(User.department_id == department_id).all()
        
        user_ids = [user.id for user in users_in_scope]
        
        if not user_ids:
            return {"recent_logins": 0, "avg_session_duration": None}
        
        # Get recent login count
        recent_logins = self.db.query(func.count(UserSession.id)).filter(
            UserSession.user_id.in_(user_ids),
            UserSession.started_at >= cutoff_date
        ).scalar() or 0
        
        # Calculate average session duration
        session_durations = self.db.query(
            func.extract('epoch', func.coalesce(UserSession.ended_at, UserSession.last_activity_at) - UserSession.started_at)
        ).filter(
            UserSession.user_id.in_(user_ids),
            UserSession.started_at >= cutoff_date
        ).all()
        
        if session_durations:
            avg_duration_seconds = sum(duration[0] for duration in session_durations if duration[0]) / len(session_durations)
            avg_duration_minutes = avg_duration_seconds / 60
        else:
            avg_duration_minutes = None
        
        return {
            "recent_logins": recent_logins,
            "avg_session_duration": avg_duration_minutes
        }
    
    def _get_most_active_users(self, department_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most active users in department"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        user_activity = self.db.query(
            User.id,
            User.full_name,
            User.job_title,
            func.count(UserSession.id).label('session_count'),
            func.max(UserSession.started_at).label('last_login')
        ).join(UserSession).filter(
            User.department_id == department_id,
            UserSession.started_at >= cutoff_date
        ).group_by(User.id, User.full_name, User.job_title).order_by(
            desc('session_count')
        ).limit(limit).all()
        
        return [
            {
                "user_id": user.id,
                "full_name": user.full_name,
                "job_title": user.job_title,
                "session_count": user.session_count,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            for user in user_activity
        ]
    
    def _get_least_active_users(self, department_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get least active users in department"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Get users with no recent activity
        inactive_users = self.db.query(User).filter(
            User.department_id == department_id,
            User.is_active == True,
            ~User.id.in_(
                self.db.query(UserSession.user_id).filter(
                    UserSession.started_at >= cutoff_date
                ).distinct()
            )
        ).limit(limit).all()
        
        return [
            {
                "user_id": user.id,
                "full_name": user.full_name,
                "job_title": user.job_title,
                "session_count": 0,
                "last_login": user.last_login_at.isoformat() if user.last_login_at else None
            }
            for user in inactive_users
        ]
    
    def _get_training_completion_rate(self, department_id: int) -> Optional[float]:
        """Get training completion rate for department (placeholder for TMS integration)"""
        # This would integrate with the Training Management System
        # For now, return a placeholder calculation
        users_in_dept = self.db.query(func.count(User.id)).filter(
            User.department_id == department_id,
            User.is_active == True
        ).scalar() or 0
        
        if users_in_dept == 0:
            return None
        
        # Placeholder: assume 85% completion rate for demo
        return 85.0
    
    def _get_quality_events_count(self, department_id: int) -> int:
        """Get quality events count for department (placeholder for QRM integration)"""
        # This would integrate with the Quality Risk Management System
        # For now, return a placeholder count
        return 0  # Would query quality_events table when QRM is integrated
    
    def _get_organization_training_completion_rate(self, organization_id: int) -> Optional[float]:
        """Get average training completion rate across organization"""
        # Placeholder for organization-wide training metrics
        return 82.5
    
    def _get_organization_quality_events_count(self, organization_id: int) -> int:
        """Get total quality events count for organization"""
        # Placeholder for organization-wide quality events
        return 0
    
    def _calculate_department_productivity_score(self, department: Department) -> float:
        """Calculate productivity score for department (example algorithm)"""
        # Example productivity calculation based on available metrics
        user_count = len(department.users)
        if user_count == 0:
            return 0.0
        
        # Get recent activity
        activity_metrics = self._get_department_activity_metrics(department.id, include_children=False)
        recent_logins = activity_metrics["recent_logins"]
        
        # Calculate base score (0-100)
        base_score = min(100, (recent_logins / user_count) * 10) if user_count > 0 else 0
        
        # Adjust for department type
        type_multipliers = {
            "operational": 1.0,
            "quality": 1.1,  # Quality departments are critical
            "administrative": 0.9,
            "research": 1.05
        }
        
        multiplier = type_multipliers.get(department.department_type, 1.0)
        
        return round(base_score * multiplier, 2)
    
    def _get_daily_login_trends(self, department_id: int, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Get daily login counts for trend analysis"""
        daily_logins = self.db.query(
            func.date(UserSession.started_at).label('date'),
            func.count(UserSession.id).label('login_count')
        ).join(User).filter(
            User.department_id == department_id,
            UserSession.started_at >= start_date,
            UserSession.started_at <= end_date
        ).group_by(func.date(UserSession.started_at)).all()
        
        return {str(date): count for date, count in daily_logins}
    
    def _get_weekly_activity_trends(self, department_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get weekly activity trends"""
        # Group by week and calculate metrics
        weekly_data = []
        current_date = start_date
        
        while current_date < end_date:
            week_end = min(current_date + timedelta(days=7), end_date)
            
            week_logins = self.db.query(func.count(UserSession.id)).join(User).filter(
                User.department_id == department_id,
                UserSession.started_at >= current_date,
                UserSession.started_at < week_end
            ).scalar() or 0
            
            weekly_data.append({
                "week_start": current_date.isoformat(),
                "week_end": week_end.isoformat(),
                "login_count": week_logins
            })
            
            current_date = week_end
        
        return weekly_data
    
    def _get_user_growth_trends(self, department_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get user growth trends over time"""
        # This would track user additions/removals over time
        # For now, return current user count
        current_users = self.db.query(func.count(User.id)).filter(
            User.department_id == department_id,
            User.is_active == True
        ).scalar() or 0
        
        return [
            {
                "date": start_date.isoformat(),
                "total_users": max(0, current_users - 5)  # Placeholder calculation
            },
            {
                "date": end_date.isoformat(),
                "total_users": current_users
            }
        ]