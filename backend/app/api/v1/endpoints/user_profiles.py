# QMS User Profile API Endpoints - Phase A Sprint 1
# FastAPI endpoints for user profile management

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user_management.user_profile import (
    UserProfileResponse, UserProfileUpdate, UserPreferenceSchema,
    UserActivitySummary
)
from datetime import datetime
from app.services.user_management.user_profile_service import UserProfileService

router = APIRouter()


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's complete profile including preferences and supervisor info
    """
    service = UserProfileService(db, current_user)
    return service.get_user_profile(current_user.id)


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get any user's profile (requires appropriate permissions)
    
    Permissions required:
    - user.view_profiles: Can view other users' profiles
    - Users can always view their own profile
    """
    service = UserProfileService(db, current_user)
    return service.get_user_profile(user_id)


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information
    
    Updatable fields:
    - phone_number: Contact phone number
    - job_title: Current job title
    - hire_date: Employee hire date
    - employee_id: Unique employee identifier
    - supervisor_id: ID of direct supervisor
    """
    service = UserProfileService(db, current_user)
    return service.update_profile(current_user.id, profile_data)


@router.put("/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: int,
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update any user's profile (requires appropriate permissions)
    
    Permissions required:
    - user.edit_profiles: Can edit other users' profiles
    """
    service = UserProfileService(db, current_user)
    return service.update_profile(user_id, profile_data)


@router.post("/me/profile/avatar")
async def upload_my_profile_picture(
    file: UploadFile = File(..., description="Profile picture image file (JPEG, PNG, WebP)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload profile picture for current user
    
    Requirements:
    - File types: JPEG, PNG, WebP
    - Maximum size: 5MB
    - Image will be resized to 400x400 pixels
    """
    service = UserProfileService(db, current_user)
    return service.upload_profile_picture(current_user.id, file)


@router.post("/{user_id}/profile/avatar")
async def upload_user_profile_picture(
    user_id: int,
    file: UploadFile = File(..., description="Profile picture image file"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload profile picture for any user (requires appropriate permissions)
    
    Permissions required:
    - user.edit_profiles: Can edit other users' profiles
    """
    service = UserProfileService(db, current_user)
    return service.upload_profile_picture(user_id, file)


@router.get("/me/preferences", response_model=List[UserPreferenceSchema])
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's preferences and settings
    """
    service = UserProfileService(db, current_user)
    return service.get_user_preferences(current_user.id)


@router.put("/me/preferences/{preference_key}", response_model=UserPreferenceSchema)
async def update_my_preference(
    preference_key: str,
    preference_value: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update or create a user preference
    
    Common preference keys:
    - theme: 'light' or 'dark'
    - language: 'en', 'es', 'fr', etc.
    - timezone: 'UTC', 'America/New_York', etc.
    - notifications_email: 'true' or 'false'
    - dashboard_layout: 'compact' or 'expanded'
    """
    service = UserProfileService(db, current_user)
    return service.update_user_preference(current_user.id, preference_key, preference_value)


@router.get("/{user_id}/preferences", response_model=List[UserPreferenceSchema])
async def get_user_preferences(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get any user's preferences (requires appropriate permissions)
    
    Permissions required:
    - user.view_profiles: Can view other users' preferences
    """
    service = UserProfileService(db, current_user)
    return service.get_user_preferences(user_id)


@router.get("/me/activity", response_model=UserActivitySummary)
async def get_my_activity_summary(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's activity summary for the specified period
    
    Includes:
    - Total login sessions
    - Total active time
    - Login frequency
    - Most active hour of day
    - Device type breakdown
    """
    service = UserProfileService(db, current_user)
    return service.get_user_activity_summary(current_user.id, days)


@router.get("/{user_id}/activity", response_model=UserActivitySummary)
async def get_user_activity_summary(
    user_id: int,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get any user's activity summary (requires appropriate permissions)
    
    Permissions required:
    - user.view_activity: Can view other users' activity
    """
    service = UserProfileService(db, current_user)
    return service.get_user_activity_summary(user_id, days)


@router.delete("/me/profile/avatar")
async def delete_my_profile_picture(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user's profile picture
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if user and user.profile_picture_url:
        # Delete file and update database
        service = UserProfileService(db, current_user)
        service._delete_old_profile_picture(user.profile_picture_url)
        
        user.profile_picture_url = None
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Profile picture deleted successfully"}
    else:
        raise HTTPException(
            status_code=404,
            detail="No profile picture found"
        )


# Health check endpoint for user profile service
@router.get("/health")
async def user_profiles_health():
    """
    Health check endpoint for user profile service
    """
    return {
        "service": "user_profiles",
        "status": "healthy",
        "version": "1.0.0",
        "features": [
            "profile_management",
            "preference_settings", 
            "activity_tracking",
            "profile_pictures"
        ]
    }