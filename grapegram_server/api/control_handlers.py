from logging import getLogger

from fastapi import APIRouter

from services.singleton import SingletonMeta


logger = getLogger(__name__)
control_router = APIRouter()


class NgrokControl(metaclass=SingletonMeta):
    def __init__(self):
        self.url = None


@control_router.get("/")
async def get_chats():
    return {"public_url": NgrokControl().url}
