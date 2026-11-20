from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.app.database.session import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.entities import User, Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    category: Optional[str] = "info"
    link: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    unread_count: int
    total_count: int
    notifications: List[NotificationResponse]

class NotificationCreate(BaseModel):
    title: str
    message: str
    category: Optional[str] = "info"
    link: Optional[str] = None

@router.get("", response_model=NotificationListResponse)
def get_user_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .count()
    )
    return NotificationListResponse(
        unread_count=unread_count,
        total_count=len(notifications),
        notifications=notifications
    )

@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": "Notification marked as read", "id": notification_id}

@router.put("/read-all")
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .update({Notification.is_read: True})
    )
    db.commit()
    return {"message": f"{updated} notifications marked as read"}
