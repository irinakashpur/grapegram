"""File with settings and configs for the project"""
from envparse import Env

env = Env()

POSTGRESQL_URL = env.str(
    "POSTGRESQL_URL",
    default="postgresql+asyncpg://postgres:postgres@0.0.0.0:5432/postgres",
)  # connect string for the real database
MONGODB_URL = env.str(
    "MONGODB_URL",
    default="mongodb://mongo:mongo@0.0.0.0/",
)  # connect string for the real database


APP_HOST = env.int("APP_HOST", default="0.0.0.0")
APP_PORT = env.int("APP_PORT", default=8000)

SECRET_KEY: str = env.str(
    "SECRET_KEY", default="ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg="
)
ALGORITHM: str = env.str("ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = env.int(
    "ACCESS_TOKEN_EXPIRE_MINUTES", default=60 * 24
)
DEBUG = True


ngrok_auth_token = "2PyF7BNG8iJwtFkWwB6kBGqlGyS_2vvajPPMfkeoD4fJ442JW"
