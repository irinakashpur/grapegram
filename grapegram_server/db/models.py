import uuid
import datetime
from enum import Enum

from sqlalchemy import Table
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from bson.objectid import ObjectId
from pydantic import BaseModel
from pydantic import Field

##############################
# BLOCK WITH DATABASE MODELS #
##############################

# PostgreSQL

Base = declarative_base()

chat_user = Table(
    "chat_user",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("chat_id", UUID(as_uuid=True), ForeignKey("chat.chat_id")),
    Column("user_id", UUID(as_uuid=True), ForeignKey("user.user_id")),
)


class User(Base):
    __tablename__ = "user"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean(), default=False)
    last_seen = Column(DateTime, default=datetime.datetime.now())
    hashed_password = Column(String, nullable=False)

    chats = relationship(
        "Chat", secondary=chat_user, lazy="selectin", back_populates="users"
    )
    # chats = relationship('Chat', secondary=chat_user, lazy="dynamic", back_populates='users')


class ChatType(str, Enum):
    PRIVATE = "PRIVATE"
    GROUP = "GROUP"
    PROTECTED = "PROTECTED"


class Chat(Base):
    __tablename__ = "chat"

    chat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_type = Column(ARRAY(String))
    name = Column(String(), nullable=True)

    users = relationship(
        "User", secondary=chat_user, lazy="selectin", back_populates="chats"
    )


# MongoDB


class MessageType(str, Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

    class Config:
        # allow_population_by_field_name = True
        json_encoders = {ObjectId: str}


class ChatMessage(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    message_type: MessageType = Field(default=MessageType.USER)
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    user_id: str
    text: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        use_enum_values = True
