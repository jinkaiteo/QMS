# QMS User Profile Service - Phase A Sprint 1
# Service layer for user profile management

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from fastapi import UploadFile, HTTPException, status
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import uuid
import secrets
from PIL import Image
import io

from app.models.user import User, UserSession
from app.models.user_management.user_profile import UserPreference
from app.schemas.user_management.user_profile import (
    UserProfileCreate, UserProfileUpdate, UserProfileResponse,
    UserActivitySummary, UserPreferenceSchema
)
from app.core.security import audit_logger
from app.core.config import settings


class UserProfileService:
    """Service for managing user profiles and preferences"""
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    def get_user_profile(self, user_id: int) -> UserProfileResponse:
        """Get complete user profile with preferences"""
        # Check permissions
        if user_id != self.current_user.id and not self.current_user.has_permission("user.view_profiles", "core"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user profile"
            )
        
        user = self.db.query(User).filter(
            User.id == user_id,
            User.is_deleted == False
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user preferences
        preferences = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.is_deleted == False
        ).all()
        
        # Get supervisor info if exists
        supervisor = None
        if user.supervisor_id:
            supervisor = self.db.query(User).filter(User.id == user.supervisor_id).first()
        
        return UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone_number=user.phone_number,
            job_title=user.job_title,
            hire_date=user.hire_date,
            employee_id=user.employee_id,
            supervisor_id=user.supervisor_id,
            profile_picture_url=user.profile_picture_url,
            last_login_at=user.last_login_at,
            login_count=user.login_count or 0,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            preferences=[UserPreferenceSchema.from_orm(pref) for pref in preferences],
            supervisor={
                "id": supervisor.id,
                "username": supervisor.username,
                "full_name": supervisor.full_name,
                "job_title": supervisor.job_title,
                "profile_picture_url": supervisor.profile_picture_url
            } if supervisor else None
        )
    
    def update_profile(self, user_id: int, profile_data: UserProfileUpdate) -> UserProfileResponse:
        """Update user profile information"""
        # Check permissions
        if user_id != self.current_user.id and not self.current_user.has_permission("user.edit_profiles", "core"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to edit user profile"
            )
        
        user = self.db.query(User).filter(
            User.id == user_id,
            User.is_deleted == False
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate employee_id uniqueness
        if profile_data.employee_id and profile_data.employee_id != user.employee_id:
            existing_user = self.db.query(User).filter(
                User.employee_id == profile_data.employee_id,
                User.id != user_id,
                User.is_deleted == False
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Employee ID already exists"
                )
        
        # Validate supervisor (can't supervise themselves)
        if profile_data.supervisor_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User cannot supervise themselves"
            )
        
        # Update user fields
        update_fields = profile_data.dict(exclude_unset=True)
        for field, value in update_fields.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Log profile update
        audit_logger.log_user_management_event(
            admin_user_id=self.current_user.id,
            target_user_id=user_id,
            event_type="profile_updated",
            details=update_fields
        )
        
        return self.get_user_profile(user_id)
    
    def upload_profile_picture(self, user_id: int, file: UploadFile) -> Dict[str, str]:
        """Upload and process user profile picture"""
        # Check permissions
        if user_id != self.current_user.id and not self.current_user.has_permission("user.edit_profiles", "core"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to upload profile picture"
            )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG, PNG, and WebP images are allowed"
            )
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size cannot exceed 5MB"
            )
        
        try:
            # Read and process image
            image_data = file.file.read()
            image = Image.open(io.BytesIO(image_data))
            
            # Resize image to standard size (400x400)
            image = image.convert('RGB')
            image = image.resize((400, 400), Image.Resampling.LANCZOS)
            
            # Generate unique filename
            file_extension = file.content_type.split('/')[-1]
            filename = f"profile_{user_id}_{uuid.uuid4().hex}.{file_extension}"
            
            # Save to storage directory
            storage_dir = os.path.join(settings.MEDIA_ROOT, "profile_pictures")
            os.makedirs(storage_dir, exist_ok=True)
            
            file_path = os.path.join(storage_dir, filename)
            image.save(file_path, quality=85, optimize=True)
            
            # Update user profile picture URL
            picture_url = f"/media/profile_pictures/{filename}"
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                # Delete old profile picture if exists
                if user.profile_picture_url:
                    self._delete_old_profile_picture(user.profile_picture_url)
                
                user.profile_picture_url = picture_url
                user.updated_at = datetime.utcnow()
                self.db.commit()
            
            # Log profile picture upload
            audit_logger.log_user_management_event(
                admin_user_id=self.current_user.id,
                target_user_id=user_id,
                event_type="profile_picture_uploaded",
                details={"filename": filename, "size": file.size}
            )
            
            return {
                "profile_picture_url": picture_url,
                "message": "Profile picture uploaded successfully"
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process image: {str(e)}"
            )
    
    def get_user_preferences(self, user_id: int) -> List[UserPreferenceSchema]:
        """Get user preferences"""
        # Check permissions
        if user_id != self.current_user.id and not self.current_user.has_permission("user.view_profiles", "core"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user preferences"
            )
        
        preferences = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.is_deleted == False
        ).all()
        
        return [UserPreferenceSchema.from_orm(pref) for pref in preferences]
    
    def update_user_preference(self, user_id: int, preference_key: str, preference_value: str) -> UserPreferenceSchema:
        """Update or create user preference"""
        # Check permissions
        if user_id != self.current_user.id and not self.current_user.has_permission("user.edit_profiles", "core"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update user preferences"
            )
        
        # Find existing preference or create new one
        preference = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_key == preference_key,
            UserPreference.is_deleted == False
        ).first()
        
        if preference:
            preference.preference_value = preference_value
            preference.updated_at = datetime.utcnow()
        else:
            preference = UserPreference(
                user_id=user_id,
                preference_key=preference_key,
                preference_value=preference_value
            )
            self.db.add(preference)
        
        self.db.commit()
        return UserPreferenceSchema.from_orm(preference)
    
    def get_user_activity_summary(self, user_id: int, days: int = 30) -> UserActivitySummary:
        """Get user activity summary for specified period"""
        # Check permissions
        if user_id != self.current_user.id and not self.current_user.has_permission("user.view_activity", "core"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user activity"
            )
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get user sessions for the period
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.started_at >= cutoff_date
        ).all()
        
        # Calculate metrics
        total_sessions = len(sessions)
        total_active_time = sum([
            (session.ended_at or session.last_activity_at) - session.started_at
            for session in sessions
        ], timedelta()).total_seconds() / 60  # Convert to minutes
        
        login_frequency = total_sessions / days if days > 0 else 0
        
        # Get last login
        user = self.db.query(User).filter(User.id == user_id).first()
        last_login = user.last_login_at if user else None
        
        # Calculate most active hour
        most_active_hour = None
        if sessions:
            hour_counts = {}
            for session in sessions:
                hour = session.started_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            most_active_hour = max(hour_counts, key=hour_counts.get)
        
        # Device breakdown from user agents
        device_types = {}
        for session in sessions:
            if session.user_agent:
                device_type = self._classify_user_agent(session.user_agent)
                device_types[device_type] = device_types.get(device_type, 0) + 1
        
        return UserActivitySummary(
            user_id=user_id,
            period_days=days,
            total_sessions=total_sessions,
            total_active_time_minutes=int(total_active_time),
            login_frequency=round(login_frequency, 2),
            last_login=last_login,
            most_active_hour=most_active_hour,
            device_types=device_types
        )
    
    def _delete_old_profile_picture(self, picture_url: str):
        """Delete old profile picture file"""
        try:
            if picture_url.startswith('/media/'):
                file_path = os.path.join(settings.MEDIA_ROOT, picture_url[7:])  # Remove '/media/'
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception:
            # Log error but don't fail the operation
            pass
    
    def _classify_user_agent(self, user_agent: str) -> str:
        """Classify user agent string into device type"""
        user_agent_lower = user_agent.lower()
        
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower or 'iphone' in user_agent_lower:
            return 'Mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            return 'Tablet'
        elif 'bot' in user_agent_lower or 'crawler' in user_agent_lower:
            return 'Bot'
        else:
            return 'Desktop'


class UserActivityService:
    """Service for tracking and managing user activity"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_user_login(self, user: User, ip_address: str, user_agent: str) -> UserSession:
        """Track user login and create session"""
        # Create new session
        session_token = secrets.token_urlsafe(32)
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            started_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow()
        )
        
        self.db.add(session)
        
        # Update user login statistics
        user.last_login_at = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        
        self.db.commit()
        
        return session
    
    def update_session_activity(self, session_token: str) -> bool:
        """Update session last activity timestamp"""
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.last_activity_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def end_user_session(self, session_token: str) -> bool:
        """End user session (logout)"""
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.ended_at = datetime.utcnow()
            session.is_active = False
            self.db.commit()
            return True
        
        return False
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up expired sessions"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        expired_sessions = self.db.query(UserSession).filter(
            UserSession.is_active == True,
            UserSession.last_activity_at < cutoff_time
        ).all()
        
        for session in expired_sessions:
            session.is_active = False
            session.ended_at = datetime.utcnow()
        
        self.db.commit()
        
        return len(expired_sessions)