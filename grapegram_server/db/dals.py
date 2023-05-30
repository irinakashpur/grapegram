from typing import Union
from uuid import UUID
from logging import getLogger

from sqlalchemy import and_
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from bson.objectid import ObjectId
from fastapi.encoders import jsonable_encoder

from db.models import User
from db.models import MessageType
from db.models import ChatType
from db.models import ChatMessage
from db.models import Chat
from hashing import Crypter


logger = getLogger(__name__)

###########################################################
# BLOCK FOR INTERACTION WITH DATABASE IN BUSINESS CONTEXT #
###########################################################


class UserDAL:
    """Data Access Layer for operating user info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_all_users(self):
        query = select(User)
        res = await self.db_session.execute(query)
        user_row = res.fetchall()
        return user_row

    async def create_user(
        self,
        username: str,
        hashed_password: str,
    ) -> User:
        new_user = User(
            username=username,
            hashed_password=hashed_password,
        )
        self.db_session.add(new_user)
        await self.db_session.flush()
        return new_user

    async def delete_user(self, user_id: UUID) -> Union[UUID, None]:
        query = (
            update(User)
            .where(and_(User.user_id == user_id, User.is_active == True))
            .values(is_active=False)
            .returning(User.user_id)
        )
        res = await self.db_session.execute(query)
        deleted_user_id_row = res.fetchone()
        if deleted_user_id_row is not None:
            return deleted_user_id_row[0]

    async def get_user_by_id(self, user_id: UUID) -> Union[User, None]:
        query = select(User).where(User.user_id == user_id)
        res = await self.db_session.execute(query)
        user_row = res.fetchone()
        if user_row is not None:
            return user_row[0]

    async def get_user_by_username(self, username: str) -> Union[User, None]:
        query = select(User).where(User.username == username)
        res = await self.db_session.execute(query)
        user_row = res.fetchone()
        if user_row is not None:
            return user_row[0]

    async def update_user(self, user_id: UUID, **kwargs) -> Union[UUID, None]:
        query = (
            update(User)
            .where(and_(User.user_id == user_id, User.is_active == True))
            .values(kwargs)
            .returning(User.user_id)
        )
        res = await self.db_session.execute(query)
        update_user_id_row = res.fetchone()
        if update_user_id_row is not None:
            return update_user_id_row[0]


class ChatDAL:
    def __init__(self, db_session, mongodb_client):
        self.db_session = db_session
        self.mongodb_client = mongodb_client

    async def get_chat_by_id(self, chat_id: UUID) -> Union[Chat, None]:
        # async with self.db_session.begin():
        query = select(Chat).where(Chat.chat_id == chat_id)
        res = await self.db_session.execute(query)
        chat_row = res.fetchone()
        if chat_row is not None:
            return chat_row[0]

    async def create_chat(self, chat_type: ChatType):
        new_chat = Chat(
            chat_type=(chat_type.value,),
        )

        self.db_session.add(new_chat)
        await self.db_session.flush()

        collection = self.get_chat_collection(new_chat.chat_id)
        message = ChatMessage(
            text="Start Chat", user_id="", message_type=MessageType.SYSTEM
        )
        collection.insert_one(jsonable_encoder(message))

        return new_chat

    async def add_user_to_chat(self, chat_id: UUID, user_id: UUID):
        user_dal = UserDAL(self.db_session)

        user = await user_dal.get_user_by_id(user_id)
        chat = await self.get_chat_by_id(chat_id)

        chat.users.append(user)

        self.db_session.add(chat)

    def add_message(self, chat_id: UUID, user_id: UUID, text: str):
        collection = self.get_chat_collection(chat_id)
        message = ChatMessage(user_id=str(user_id), text=text)
        collection.insert_one(jsonable_encoder(message))
        return message.id

    def get_message(self, chat_id: UUID, message_id: str):
        collection = self.get_chat_collection(chat_id)
        mongo_message = collection.find_one({"_id": str(message_id)})
        logger.warn(mongo_message)
        if mongo_message is None:
            return None
        return ChatMessage(**mongo_message)

    def get_messages_that_upper_then_origin_message(
        self, chat_id: UUID, origin_message_id: str, number: int
    ):
        collection = self.get_chat_collection(chat_id)

        messages = (
            collection.find({"_id": {"$lt": str(origin_message_id)}})
            .sort("_id", -1)
            .limit(number)
            .sort("_id", 1)
        )

        chat_messages = []
        for message in messages:
            chat_messages.append(ChatMessage(**message))

        return chat_messages

    def get_chat_collection(self, chat_id: UUID):
        return self.mongodb_client[str(chat_id)]

    async def get_all_user_chats(self, user_id: UUID):
        user_dal = UserDAL(self.db_session)
        user = await user_dal.get_user_by_id(user_id)
        return user.chats

    async def get_all_user_filtered_chats(self, user_id: UUID):
        chats = await self.get_all_user_chats(user_id)
        types = (ChatType.GROUP, ChatType.PRIVATE)

        result = {}
        for _type in types:
            result[_type] = []

        for chat in chats:
            chat_type = chat.chat_type[0]
            if chat_type not in types:
                continue

            result[chat_type].append(chat)

        return result

    async def get_chat_name(self, chat_id: UUID, user_id: UUID) -> str:
        chat = await self.get_chat_by_id(chat_id)

        if ChatType.PRIVATE not in chat.chat_type:
            return chat.name or ""

        other_user = None
        for user in chat.users:
            if user.user_id != user_id:
                other_user = user
                break

        return other_user.username

    def get_last_message_in_chat(self, chat_id: UUID):
        collection = self.get_chat_collection(chat_id)
        message = collection.find_one(sort=[("_id", -1)])
        logger.warn(f"{message=}")
        return ChatMessage(**message)
