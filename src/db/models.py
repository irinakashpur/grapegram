import uuid

from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base


##############################
# BLOCK WITH DATABASE MODELS #
##############################

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(32), nuleable=False, unique=True)
    password = Column(String(32), nuleable=False)
    is_active = Column(Boolean(), default=True)