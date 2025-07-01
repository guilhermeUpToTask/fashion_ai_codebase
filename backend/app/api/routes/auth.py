from datetime import timedelta
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from core import user_crud
from api.deps import CurrentUser, SessionDep
from core import security
from core.config import settings
from models.user import Token, UserCreate, UserPublic, UserRegister

router = APIRouter(tags=["auth"], prefix="/auth")

@router.post("/login", response_model=Token)
def login_acces_token(
    session:SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
)-> Token:
    user = user_crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive User")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )
    
@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    return current_user

@router.get("/login/refresh-token", response_model=Token)
def refresh_token(
    session: SessionDep, current_user: CurrentUser
) -> Token:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            current_user.id, expires_delta=access_token_expires
        )
    )

@router.post("/register", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    user = user_crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system"
        )
    user_create = UserCreate.model_validate(user_in)
    user = user_crud.create_user(session=session, user_create=user_create)
    return user