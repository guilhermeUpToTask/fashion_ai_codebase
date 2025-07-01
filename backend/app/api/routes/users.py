import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core import user_crud
from api.deps import (
    CurrentUser, SessionDep, get_current_admin_user
)

from core.config import settings
from core.security import verify_password
from models.user import(
    Message,
    UpdatePassword,
    UserPublic,
    UserRole,
    UserUpdate,
    UsersPublic,
    UserUpdateMe
)

router = APIRouter(prefix="/users", tags=["users"])

# User routes
@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session:SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> UserPublic: 
    
    if user_in.email:
        existing_user = user_crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
            
    user = user_crud.update_user(
        session=session, db_user=current_user, user_in=user_in
    )
    return user

@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session:SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Message:
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
        
    user_crud.update_user(
        session=session,
        db_user=current_user,
        user_in=UserUpdate(password=body.new_password),
    )
    
    return Message(message="password updated sucessfully")

@router.get("/me", response_model=UserPublic)
def read_user_me(current_user:CurrentUser):
    return current_user

@router.delete("/me", response_model= Message)
def delete_user_me(session:SessionDep, current_user:CurrentUser) -> Message:
    user_crud.delete_user(session=session, db_user=current_user)
    return Message(message="user deleted successfully")


#Private routes
@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    user = user_crud.get_user_by_id(session=session, user_id=user_id)
    if user == current_user:
        return user
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    if not user:
        raise HTTPException(
            status_code=404, detail="The user with this id does not exist in the system"
        )
    return user

@router.get("/", response_model=UsersPublic, dependencies=[Depends(get_current_admin_user)])
def read_users(session:SessionDep, skip: int = 0, limit:int = 100) -> Any:
    
    count = user_crud.get_user_count(session=session)
    users = user_crud.get_users(session=session, skip=skip, limit=limit)

    return UsersPublic(data=users, count=count)

@router.patch("/{user_id}",dependencies=[Depends(get_current_admin_user)],response_model=UserPublic,)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    db_user = user_crud.get_user_by_id(session=session, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = user_crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = user_crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_admin_user)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    user = user_crud.get_user_by_id(session=session, user_id=user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Admin users are not allowed to delete themselves"
        )

    user_crud.delete_user(session=session, db_user=user)
    
    return Message(message="User deleted successfully")