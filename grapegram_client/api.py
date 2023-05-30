import eel
import json
import requests

from services.containers import User, Server, Chats
from services.models import Token, PrivateChat, GroupChat


Unauthorized = 401


def pre_request():
    user = User()
    if user.token is None:
        eel.redirect_to_login()
        return False

    return True


def collect_headers(headers):
    user = User()
    headers = headers.copy()
    headers.update(
        {
            "accept": "application/json",
            "Authorization": f"{user.token.token_type} {user.token.access_token}",
            "ngrok-skip-browser-warning": "69420",
        }
    )
    print(f"{headers=}")
    return headers


def post(*args, **kwargs):
    if not pre_request():
        return None

    headers = collect_headers(kwargs.get("headers", dict()))

    return requests.post(*args, **kwargs, headers=headers)


def get(*args, **kwargs):
    if not pre_request():
        return None

    headers = collect_headers(kwargs.get("headers", dict()))

    return requests.get(*args, **kwargs, headers=headers)


def login(server_url, username, password):
    login_url = f"{server_url}/auth/token"
    response = requests.post(
        login_url, data={"username": username, "password": password}
    )

    if response.status_code == Unauthorized:
        return None
    elif response.status_code != 200:
        return None

    return Token(**response.json())


def sign_up(server_url, username, password):
    sign_up_url = f"{server_url}/user/"
    response = requests.post(
        sign_up_url, json={"username": username, "password": password}
    )

    if response.status_code == 200:
        return True

    return False


def get_all_users():
    server = Server()
    url = f"{server.url}/user/all"

    response = get(url=url)
    return response.json()


def get_me():
    server = Server()
    url = f"{server.url}/user/me"

    response = get(url=url)
    return response.json()


def get_user_by_id(user_id):
    server = Server()
    url = f"{server.url}/user/"

    response = get(url=url, params={"user_id": user_id})
    return response.json()


def update_chats():
    server = Server()
    url = f"{server.url}/chat/"
    print("update_chats", url)
    response = get(url=url)
    data = response.json()
    print("update_chats data", data)

    chats = []
    for raw_chat in data["private_chats"]:
        chats.append(PrivateChat(**raw_chat))

    for raw_chat in data["group_chats"]:
        chats.append(GroupChat(**raw_chat))

    Chats().chats = chats


def get_last_message(chat_id):
    server = Server()
    url = f"{server.url}/chat/get_last_message"
    response = get(url=url, params={"chat_id": chat_id})
    return response.json()


def send_message(chat_id, text):
    server = Server()
    url = f"{server.url}/chat/message"
    response = post(url=url, params={"chat_id": chat_id, "text": text})


def select_chat():
    chats = Chats()
    server = Server()
    url = f"{server.url}/chat/connect_to_chat"
    response = post(url=url, params={"chat_id": chats.current_chat.chat_id})


def get_message_by_id(message_id):
    chats = Chats()
    server = Server()
    url = f"{server.url}/chat/message"
    response = get(
        url=url,
        params={"chat_id": chats.current_chat.chat_id, "message_id": message_id},
    )
    return response.json()


def get_upper_messages():
    chats = Chats()
    server = Server()
    url = f"{server.url}/chat/get_upper_messages"
    print(
        "get_upper_messages",
        {"chat_id": chats.current_chat.chat_id, "message_id": chats.upper_message_id},
    )
    response = get(
        url=url,
        params={
            "chat_id": chats.current_chat.chat_id,
            "message_id": chats.upper_message_id,
        },
    )
    print(f"{response.json()=}")
    return response.json()


def crate_chat(user_id):
    server = Server()
    url = f"{server.url}/chat/"
    response = post(url=url, params={"friend_id": user_id})
