from enum import Enum
from sqlmodel import SQLModel, Field
import uuid
from pydantic import EmailStr

class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.CLIENT, nullable=False) 
    
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)

class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)

class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)

class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)

class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)

class User(UserBase, table=True):
    __tablename__ = "user" # type: ignore
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str

class UserPublic(UserBase):
    id:uuid.UUID
    
class UsersPublic(SQLModel):
    data:list[UserPublic]
    count: int

class Message (SQLModel):
    message: str
    
class TokenPayload(SQLModel):
    sub: str | None = None
    
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
    