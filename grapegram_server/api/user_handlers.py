from logging import getLogger
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.actions.auth import get_current_user_from_token
from api.actions.user import _create_new_user
from api.actions.user import _delete_user
from api.actions.user import _get_user_by_id
from api.schemas import DeleteUserResponse
from api.schemas import ShowUser
from api.schemas import UserCreate
from db.models import User
from db.dals import UserDAL
from db.session import get_db

logger = getLogger(__name__)

user_router = APIRouter()


@user_router.post("/", response_model=ShowUser)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)) -> ShowUser:
    logger.warn(body.username, body.password)
    try:
        return await _create_new_user(body, db)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")


@user_router.delete("/", response_model=DeleteUserResponse)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
) -> DeleteUserResponse:
    deleted_user_id = await _delete_user(user_id, db)
    if deleted_user_id is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return DeleteUserResponse(deleted_user_id=deleted_user_id)


@user_router.get("/", response_model=ShowUser)
async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
) -> ShowUser:
    user = await _get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return user


@user_router.get("/me", response_model=ShowUser)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
) -> ShowUser:
    return current_user


@user_router.get("/all")
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
):
    user_dal = UserDAL(db)
    users = []

    row_users = await user_dal.get_all_users()
    logger.warn(row_users)
    for user in row_users:
        users.append(
            ShowUser(
                user_id=user[0].user_id,
                username=user[0].username,
                is_active=user[0].is_active,
            )
        )

    return users
