from openai import OpenAI

from response import ResponseT, Code, Status


class JarvisAlphaService:
    BASE_PATH = '/jarvis_alpha'

    def __init__(self, client: OpenAI):
        self.client = client

    @staticmethod
    def process(message: str) -> ResponseT:
        return ResponseT(
            code=Code.ok,
            status=Status.ok,
            data=message
        )
