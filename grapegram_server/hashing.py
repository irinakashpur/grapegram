from passlib.context import CryptContext
from cryptography.fernet import Fernet

import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

fernet = Fernet(settings.SECRET_KEY)


class Crypter:
    @staticmethod
    def encrypt(text):
        return str(fernet.encrypt(bytes(text, "UTF-8")))

    @staticmethod
    def decrypt(text):
        return str(fernet.decrypt(bytes(text)))


class Hasher:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
