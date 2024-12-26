from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.schemas.user_schemas import UserCreate, UserResponse
from app.models.user_models import User
from app.auth import get_password_hash, get_current_user
from app.db import get_session
from sqlmodel import select
user_router = APIRouter(prefix = "/user")


# Get All Users Endpoint
@user_router.get("/get_all_users", response_model=List[UserResponse])
def get_all_users(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    users = session.exec(select(User)).all()
    return users



# Update User Endpoint
@user_router.put("/update_user/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Update fields
    user.username = user_data.username
    user.email = user_data.email
    user.hashed_password = get_password_hash(user_data.password)

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# Delete User Endpoint
@user_router.delete("/delete_user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    session.delete(user)
    session.commit()
    return None


@user_router.get("/get_current_user_details/", response_model=UserResponse)
def get_user(current_user: User = Depends(get_current_user)):
    print(type(current_user))
    return current_user