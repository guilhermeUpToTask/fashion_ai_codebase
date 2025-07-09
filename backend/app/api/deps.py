from typing import Annotated
from collections.abc import Generator
import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from core.db import engine
from core.config import settings
from models.user import TokenPayload, User
from core.vector_db.chroma_db import persistent_client
from chromadb.api import ClientAPI

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_db)]

def get_chroma_client() -> Generator[ClientAPI, None, None]:
    yield persistent_client
ChromaSessionDep = Annotated[ClientAPI, Depends(get_chroma_client)]

TokenDep = Annotated[str, Depends(reusable_oauth2)]

def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )  
    try:
        user_id = uuid.UUID(token_data.sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token payload.",
        )
    user = session.get(User, user_id)   

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def get_current_admin_user(current_user: CurrentUser) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
