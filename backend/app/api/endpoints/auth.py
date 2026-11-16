from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database.session import get_db
from backend.app.models.entities import User
from backend.app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserProfile
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.core.dependencies import get_current_user
from backend.app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    email_clean = user_in.email.strip().lower()
    
    # Check duplicate email case-insensitively
    existing = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address is already registered."
        )
    
    # Password strength validation
    if len(user_in.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters in length."
        )

    # Role validation and admin security check
    requested_role = (user_in.role or "student").strip().lower()
    if requested_role == "admin":
        if not user_in.admin_code or user_in.admin_code.strip() != settings.ADMIN_INVITE_CODE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator registration requires a valid administrator authorization code. Please enter the correct code or select Student."
            )
        role = "admin"
    else:
        role = "student"

    # Derive full name if not provided
    if user_in.full_name and user_in.full_name.strip():
        name = user_in.full_name.strip()
    else:
        name = email_clean.split('@')[0].replace('.', ' ').replace('_', ' ').title()

    new_user = User(
        email=email_clean,
        full_name=name,
        hashed_password=get_password_hash(user_in.password),
        role=role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": new_user.email, "role": new_user.role, "uid": new_user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role
    )

@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    email_clean = credentials.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been deactivated."
        )

    token = create_access_token(data={"sub": user.email, "role": user.role, "uid": user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )

@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
