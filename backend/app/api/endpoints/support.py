from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from backend.app.database.session import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.entities import User, SupportTicket

router = APIRouter(prefix="/support", tags=["Support"])

class TicketCreateRequest(BaseModel):
    subject: str
    category: str = "General Inquiry"
    priority: str = "Medium"
    message: str

class TicketReplyRequest(BaseModel):
    admin_reply: str
    status: Optional[str] = None

class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    user_id: int
    subject: str
    category: str
    priority: str
    status: str
    message: str
    admin_reply: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    payload: TicketCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket_num = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    new_ticket = SupportTicket(
        ticket_number=ticket_num,
        user_id=current_user.id,
        subject=payload.subject,
        category=payload.category,
        priority=payload.priority,
        status="Open",
        message=payload.message
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

@router.get("", response_model=List[TicketResponse])
def list_support_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Admins and Reviewers can view all tickets; Students only view their own
    if current_user.role in ["admin", "reviewer"]:
        tickets = db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).all()
    else:
        tickets = (
            db.query(SupportTicket)
            .filter(SupportTicket.user_id == current_user.id)
            .order_by(SupportTicket.created_at.desc())
            .all()
        )
    return tickets

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket_details(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    if current_user.role not in ["admin", "reviewer"] and ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this ticket")
    return ticket

@router.put("/{ticket_id}/reply", response_model=TicketResponse)
def reply_support_ticket(
    ticket_id: int,
    payload: TicketReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    if current_user.role not in ["admin", "reviewer"]:
        raise HTTPException(status_code=403, detail="Only reviewers and administrators can respond to tickets")

    ticket.admin_reply = payload.admin_reply
    if payload.status:
        ticket.status = payload.status
    else:
        ticket.status = "Resolved"
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket
