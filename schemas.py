from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, EmailStr

class UserBase(BaseModel):
    username: str = Field(max_length=50, min_length=1)
    email: EmailStr = Field(max_length=120, min_length=1)

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_file: str | None
    image_path: str


class PostBase(BaseModel):
        title: str = Field(max_length=100, min_length=1)
        content: str = Field(max_length=1000, min_length=1)

class PostCreate(PostBase):
    user_id: int # Temoprary field to associate the post with a user


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date_posted: datetime
    author: UserResponse
