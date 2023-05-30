import uvicorn
import ngrok
from fastapi import FastAPI
from fastapi.routing import APIRouter
from fastapi.middleware.cors import CORSMiddleware


import settings
from api.user_handlers import user_router
from api.chat_handlers import chat_router
from api.login_handlers import login_router
from api.control_handlers import control_router, NgrokControl


def activate_ngrok():
    try:
        addr = f"http://{settings.APP_HOST}:{settings.APP_PORT}"
        public_url = ngrok.connect(addr=addr, authtoken=settings.ngrok_auth_token).url()
        print('ngrok tunnel "{}" -> "{}"'.format(public_url, addr))

        return public_url

    except ValueError:
        print("ngrok already start")


def configure():
    # create instance of the app
    app = FastAPI(title="grapegram_server", debug=settings.DEBUG)

    # create the instance for the routes
    main_api_router = APIRouter()

    # set routes to the app instance
    main_api_router.include_router(login_router, prefix="/auth", tags=["auth"])
    main_api_router.include_router(user_router, prefix="/user", tags=["user"])
    main_api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
    main_api_router.include_router(control_router, prefix="", tags=["main"])

    app.include_router(main_api_router)

    origins = ["*"]

    app = CORSMiddleware(
        app=app,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


def main():
    ngrok_url = activate_ngrok()
    NgrokControl().url = ngrok_url
    app = configure()
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)


if __name__ == "__main__":
    main()
