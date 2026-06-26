from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from uuid import UUID
from database.models import User
from database.config import get_db
from typing import List

# Router
router = APIRouter(tags=["Users"])

# Pydantic Schemas
class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    created_at: datetime

# Dependency
async def get_current_user(token: str = Depends(), db: Session = Depends(get_db)):
    # Implementation same as auth.py
    pass

# Routes
@router.get("/", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).all()
    return users

@router.get("/{id}", response_model=UserResponse)
async def get_user(id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/{id}", response_model=UserResponse)
async def update_user(id: UUID, user_data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_data.username:
        user.username = user_data.username
    if user_data.email:
        user.email = user_data.email
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()