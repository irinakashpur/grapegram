from typing import Generator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient

import settings

##############################################
# BLOCK FOR COMMON INTERACTION WITH DATABASE #
##############################################

# create async engine for interaction with database
engine = create_async_engine(
    settings.POSTGRESQL_URL,
    future=True,
    echo=True,
    execution_options={"isolation_level": "AUTOCOMMIT"},
)

# create session for the interaction with database
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# mongodb_client = MongoClient(settings.MONGODB_URL, uuidRepresentation='standard')
mongodb_client = MongoClient(settings.MONGODB_URL)


def get_mongodb():
    return mongodb_client["grapegram"]
    # try:
    #     mongodb_client.start_session()
    #     yield mongodb_client
    # finally:
    #     mongodb_client.close()


async def get_db() -> Generator:
    """Dependency for getting async session"""
    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()
