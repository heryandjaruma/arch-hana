from typing import Union

from fastapi import FastAPI, Depends, status

from happy import HappyService
from jarvis_alpha import JarvisAlphaService
from jarvis_sigma import JarvisSigmaService

app = FastAPI()
happy = HappyService()
jarvis_alpha = JarvisAlphaService()
jarvis_sigma = JarvisSigmaService()

CHAT = "/chat"
_CHAT = "/_chat"


def _get_happy_service():
    return happy


def _get_jarvis_alpha_service():
    return jarvis_alpha


def _get_jarvis_sigma_service():
    return jarvis_sigma


@app.post(happy.BASE_PATH + CHAT, status_code=status.HTTP_200_OK)
def happy_chat(happy_service: HappyService = Depends(_get_happy_service)):
    return happy_service.validate_message(message="Hello Happy")


@app.post(jarvis_alpha.BASE_PATH + _CHAT, status_code=status.HTTP_200_OK)
def jarvis_alpha_chat(jarvis_alpha_service: JarvisAlphaService = Depends(_get_jarvis_alpha_service)):
    return jarvis_alpha_service.process(message="Hello Jarvis Alpha")


@app.post(jarvis_sigma.BASE_PATH + _CHAT, status_code=status.HTTP_200_OK)
def jarvis_sigma_chat(jarvis_alpha_service: JarvisAlphaService = Depends(_get_jarvis_sigma_service)):
    return jarvis_alpha_service.process(message="Hello Jarvis Sigma")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
