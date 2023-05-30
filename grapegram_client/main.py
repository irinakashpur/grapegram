import datetime
import eel
import uuid
import websocket
from jinja2 import Environment, BaseLoader
from threading import Thread
import json

import config
import api
from services.containers import User, Server, Chats


class Container(object):
    def __init__(self):
        ...


main_container = Container()
main_container.is_logged = False
main_container.server_url = None
main_container.user_token = None


@eel.expose
def send_message(text):
    api.send_message(Chats().current_chat.chat_id, text)


@eel.expose
def get_info():
    return {"server_url": Server().url, "username": User().username}


@eel.expose
def is_logged_in():
    return User().token is not None


def compile_message(message_id, sender_id, text, message_type, timestamp):
    sub_class = ""
    username = ""
    user = User()

    timestamp = datetime.datetime.fromisoformat(timestamp)
    timestamp = timestamp.strftime("%H:%M:%S")

    if message_type == "SYSTEM":
        sub_class = "system"
        username = "system"
    else:
        if sender_id == user.user_id:
            sub_class = "your"
            username = user.username
        else:
            sub_class = "other"
            username = api.get_user_by_id(sender_id)["username"]

    template_html = """
    <div class="message-box {{type}}">
        <div class="message-box__message">
            <input type="text" class="id" value="{{message_id}}" style="display: none;">
            <p class="message-box__message__sender"><b>{{username}}</b></p>
            <p>{{text}}<b><span class="message-box__message__time">{{timestamp}}</span></b></p>
        </div>
    </div>
    """

    rtemplate = Environment(loader=BaseLoader).from_string(template_html)

    return rtemplate.render(
        message_id=message_id,
        username=username,
        text=text,
        type=sub_class,
        timestamp=timestamp,
    )


def compile_message_from_model(message):
    return compile_message(
        message_id=message["_id"],
        message_type=message["message_type"],
        timestamp=message["timestamp"],
        sender_id=message["user_id"],
        text=message["text"],
    )


def on_message(ws, message):
    data = json.loads(message)
    print("on_message", data)

    if data["type"] == "new_message":
        message = api.get_message_by_id(data["data"]["id"])
        eel.append_message(compile_message_from_model(message))


@eel.expose
def add_history():
    if not Chats().can_load_more:
        return

    data = api.get_upper_messages()
    messages = data["messages"]
    Chats().can_load_more = bool(data["more"])

    if not messages:
        Chats().can_load_more = False
        # eel.insert_message()
        return

    Chats().upper_message_id = messages[0]["_id"]
    result = ""

    for message in messages:
        result += compile_message_from_model(message)

    eel.insert_message(result)


@eel.expose
def connect_to_ws():
    server = Server()
    url = server.url
    url = url.replace("https://", "wss://")
    url = url.replace("http://", "ws://")
    url = f"{url}/chat/ws"

    print("connect_to_ws", url)

    header = api.collect_headers({})
    print(header)
    ws = websocket.WebSocketApp(url, on_message=on_message, header=header)
    server.ws = ws

    thread = Thread(target=ws.run_forever, args=(), daemon=True)
    thread.start()


def compile_user(user):
    template_html = """
    <div class="user" onclick="selectUser(this)">
        <input type="text" class="id" value="{{user_id}}" style="display: none;">
        <div class="chat__name">{{username}}</div>
    </div>
    """

    rtemplate = Environment(loader=BaseLoader).from_string(template_html)

    return rtemplate.render(user_id=user["user_id"], username=user["username"])


@eel.expose
def get_all_user():
    users = api.get_all_users()

    result = ""
    for user in users:
        if user["user_id"] == User().user_id:
            continue

        result += compile_user(user)

    return result


@eel.expose
def create_chat(user_id):
    print("create_chat", user_id)
    api.crate_chat(user_id)


def compile_chat(chat):
    template_html = """
    <div class="chat" onclick="selectChat(this)">
        <input type="text" class="id" value="{{chat_id}}" style="display: none;">
        <div class="chat__name">{{name}}</div>
    </div>
    """

    rtemplate = Environment(loader=BaseLoader).from_string(template_html)

    return rtemplate.render(name=chat.name, chat_id=chat.chat_id)


@eel.expose
def update_chats():
    api.update_chats()

    result_chats = []
    for chat in Chats().chats:
        result_chats.append(compile_chat(chat))

    return "".join(result_chats)


@eel.expose
def select_chat(chat_id):
    origin_chat = None
    for chat in Chats().chats:
        if chat.chat_id == uuid.UUID(chat_id):
            origin_chat = chat
            break

    chats = Chats()
    chats.current_chat = origin_chat
    chats.can_load_more = True
    api.select_chat()

    message = api.get_last_message(chats.current_chat.chat_id)
    print("select_chat message:", message)
    message_html = compile_message_from_model(message)
    eel.append_message(message_html, True)

    chats.upper_message_id = message["_id"]
    print(f"{chats.upper_message_id=}")


@eel.expose
def sign_in(server_url, username, password):
    token = api.login(server_url, username, password)

    if token is None:
        return False

    Server().url = server_url
    User().token = token

    User().token = token
    user = api.get_me()
    User().user_id = user["user_id"]
    User().username = user["username"]

    return True


@eel.expose
def sign_up(server_url, username, password):
    return api.sign_up(server_url, username, password)


def main():
    eel.init("web")
    eel.start(
        "templates/home.html",
        jinja_templates="templates",
        host=config.host,
        port=config.port,
        mode="default",
        cmdline_args=[
            "--app",
        ],
    )


if __name__ == "__main__":
    main()
