from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Dog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    breed: str
    age: int
    bio: str
    owner_name: str
    photo_path: str
    pixel_photo_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Like(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    liker_dog_id: int = Field(foreign_key="dog.id")
    liked_dog_id: int = Field(foreign_key="dog.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dog_a_id: int = Field(foreign_key="dog.id")
    dog_b_id: int = Field(foreign_key="dog.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
