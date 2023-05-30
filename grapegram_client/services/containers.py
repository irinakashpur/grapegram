from services.singleton import SingletonMeta


class User(metaclass=SingletonMeta):
    def __init__(self):
        self.token = None
        self.user_id = None
        self.username = None


class Server(metaclass=SingletonMeta):
    def __init__(self):
        self.url = None
        self.ws = None


class Chats(metaclass=SingletonMeta):
    def __init__(self):
        self.chats = []
        self.current_chat = None
        self.upper_message_id = None
