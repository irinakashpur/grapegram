import re
import uuid
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import constr
from pydantic import validator
from db.models import PyObjectId
from bson.objectid import ObjectId

#########################
# BLOCK WITH API MODELS #
#########################

LETTER_MATCH_PATTERN = re.compile(r"^[a-zA-Z_\d]+$")


class TunedModel(BaseModel):
    class Config:
        """tells pydantic to convert even non dict obj to json"""

        orm_mode = True


class ShowUser(TunedModel):
    user_id: uuid.UUID
    username: str
    is_active: bool


class UserCreate(BaseModel):
    username: str
    password: str

    @validator("username")
    def validate_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value


class DeleteUserResponse(BaseModel):
    deleted_user_id: uuid.UUID


class CreatePrivateChatResponse(BaseModel):
    friend_id: uuid.UUID


class Token(BaseModel):
    access_token: str
    token_type: str


class ShowChat(BaseModel):
    chat_id: uuid.UUID
    chat_type: str
    name: str


class ShowChats(BaseModel):
    private_chats: list[ShowChat]
    group_chats: list[ShowChat]


class AddMessageResponse(BaseModel):
    chat_id: uuid.UUID
    text: str


class GetMessageResponse(BaseModel):
    chat_id: uuid.UUID
    message_id: uuid.UUID


class GetLastMessageResponse(BaseModel):
    chat_id: uuid.UUID


class MessageId(BaseModel):
    id: PyObjectId

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ControlMessage(BaseModel):
    type: str
    data: MessageId

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
