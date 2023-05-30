import uuid
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class Chat(BaseModel):
    chat_id: uuid.UUID
    chat_type: str
    name: str


class PrivateChat(Chat):
    ...


class GroupChat(Chat):
    ...
