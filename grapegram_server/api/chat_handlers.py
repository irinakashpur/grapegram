from logging import getLogger
import datetime
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import WebSocket, WebSocketDisconnect

from api.actions.auth import get_current_user_from_token
from api.actions.user import _create_new_user
from api.actions.user import _delete_user
from api.actions.user import _update_user
from api.actions.user import _get_user_by_id
from api.schemas import DeleteUserResponse
from api.schemas import ShowUser
from api.schemas import ShowChat
from api.schemas import ShowChats
from api.schemas import UserCreate
from api.schemas import AddMessageResponse
from api.schemas import CreatePrivateChatResponse
from api.schemas import GetMessageResponse
from api.schemas import GetLastMessageResponse
from api.schemas import ControlMessage
from api.schemas import MessageId
from db.models import User
from db.models import ChatType
from db.models import ChatMessage
from db.models import PyObjectId
from db.dals import ChatDAL
from db.session import get_db
from db.session import get_mongodb
from services.websocket_manager import ConnectionManager


logger = getLogger(__name__)
ws_manager = ConnectionManager()
chat_router = APIRouter()

user_to_ws = dict()


class ChatUsers:
    def __init__(self):
        self.user_to_chat = dict()
        self.chat_to_users = dict()

    def add(self, user, chat):
        try:
            self.remove(user)
        except:
            ...

        self.user_to_chat[user] = chat
        if chat not in self.chat_to_users:
            self.chat_to_users[chat] = []

        self.chat_to_users[chat].append(user)
        logger.warn("add")
        logger.warn(self.chat_to_users)
        logger.warn(self.user_to_chat)

    def remove(self, user):
        chat = self.user_to_chat[user]
        self.chat_to_users[chat].remove(user)
        del self.user_to_chat[user]
        logger.warn("remove")
        logger.warn(self.chat_to_users)
        logger.warn(self.user_to_chat)


chat_users = ChatUsers()


@chat_router.post("/")
async def create_private_chat(
    friend_id: UUID,
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncSession = Depends(get_mongodb),
    current_user: User = Depends(get_current_user_from_token),
):
    chat_dal = ChatDAL(db, mongodb)

    async with db.begin():
        chat = await chat_dal.create_chat(ChatType.PRIVATE)

        await chat_dal.add_user_to_chat(chat.chat_id, current_user.user_id)
        await chat_dal.add_user_to_chat(chat.chat_id, friend_id)


@chat_router.post("/group")
async def create_group_chat(
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncSession = Depends(get_mongodb),
    current_user: User = Depends(get_current_user_from_token),
):
    chat_dal = ChatDAL(db, mongodb)

    async with db.begin():
        chat = await chat_dal.create_chat(ChatType.PRIVATE)
        await chat_dal.add_user_to_chat(chat.chat_id, current_user.user_id)


@chat_router.get("/")
async def get_chats(
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncSession = Depends(get_mongodb),
    current_user: User = Depends(get_current_user_from_token),
) -> ShowChats:
    chat_dal = ChatDAL(db, mongodb)
    chats = await chat_dal.get_all_user_filtered_chats(current_user.user_id)
    private_chats = chats[ChatType.PRIVATE]
    group_chats = chats[ChatType.GROUP]

    result_private_chats = []
    for chat in private_chats:
        name = await chat_dal.get_chat_name(chat.chat_id, current_user.user_id)
        result_private_chats.append(
            ShowChat(
                chat_id=chat.chat_id,
                chat_type=chat.chat_type[0],
                name=name,
            )
        )

    result_group_chats = []
    for chat in group_chats:
        name = await chat_dal.get_chat_name(chat.chat_id, current_user.user_id)
        result_group_chats.append(
            ShowChat(
                chat_id=chat.chat_id,
                chat_type=chat.chat_type[0],
                name=name,
            )
        )

    return ShowChats(private_chats=result_private_chats, group_chats=result_group_chats)


@chat_router.post("/message")
async def add_message(
    chat_id: UUID,
    text: str,
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncSession = Depends(get_mongodb),
    current_user: User = Depends(get_current_user_from_token),
):
    chat_dal = ChatDAL(db, mongodb)
    message_id = chat_dal.add_message(chat_id, current_user.user_id, text)

    for user in chat_users.chat_to_users[chat_id]:
        ws = user_to_ws[user]
        message = ControlMessage(type="new_message", data=MessageId(id=message_id))
        await ws_manager.send_personal_message(message.json(), ws)


@chat_router.get("/message", response_model=ChatMessage)
async def get_message(
    chat_id: UUID,
    message_id: PyObjectId,
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncSession = Depends(get_mongodb),
    current_user: User = Depends(get_current_user_from_token),
) -> ChatMessage:
    chat_dal = ChatDAL(db, mongodb)
    logger.warn(f"{message_id=}")
    message = chat_dal.get_message(chat_id, message_id)
    logger.warn(f"{message=}")
    return message


@chat_router.get("/get_upper_messages")
async def get_upper_messages(
    chat_id: UUID,
    message_id: PyObjectId,
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncSession = Depends(get_mongodb),
    current_user: User = Depends(get_current_user_from_token),
):
    n = 100
    chat_dal = ChatDAL(db, mongodb)
    messages = chat_dal.get_messages_that_upper_then_origin_message(
        chat_id, message_id, n
    )
    return {
        "messages": messages,
        "more": not (len(messages) < n),
    }


@chat_router.get("/get_last_message", response_model=ChatMessage)
async def get_upper_messages(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncSession = Depends(get_mongodb),
    current_user: User = Depends(get_current_user_from_token),
) -> ChatMessage:
    chat_dal = ChatDAL(db, mongodb)
    return chat_dal.get_last_message_in_chat(chat_id)


@chat_router.post("/connect_to_chat")
async def connect_to_chat(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    mongodb: AsyncSession = Depends(get_mongodb),
    current_user: User = Depends(get_current_user_from_token),
):
    chat_users.add(current_user.user_id, chat_id)


@chat_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
):
    await ws_manager.connect(websocket)
    user_to_ws[current_user.user_id] = websocket
    await _update_user({"is_active": True}, current_user.user_id, db)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        await _update_user(
            {"is_active": False, "last_seen": datetime.datetime.now()},
            current_user.user_id,
            db,
        )
        del user_to_ws[current_user.user_id]
