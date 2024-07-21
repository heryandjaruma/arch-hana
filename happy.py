import time
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel

from response import ResponseT, Code, Status


class Location(BaseModel):
    latitude: int
    longitude: int


class HappyRequest(BaseModel):
    """
    Request class for Happy.
    """
    thread_id: Optional[str] = ""
    message: str
    user_agent: str
    location: Location


class HappyService:
    BASE_PATH = '/happy'

    ASSISTANT_ID = 'asst_5vxCPEMA4IRHfo9GlTSX09oV'  # Ducker assistant 🦆
    INSTRUCTIONS = 'Answer all questions with the word "duck" but expressively.'

    def __init__(self, client: OpenAI):
        self.client = client

    def chat(self, request: HappyRequest) -> ResponseT:
        """
        Chat with Happy.
        If thread_id is not defined in the body, a new thread will be created.

        :param request: Request body
        :return: message response
        """
        assistant = self.client.beta.assistants.retrieve(assistant_id=self.ASSISTANT_ID)
        if not request.thread_id:
            thread = self.client.beta.threads.create()
        else:
            thread = self.client.beta.threads.retrieve(thread_id=request.thread_id)
        message = self.client.beta.threads.messages.create(thread_id=thread.id,
                                                           role="assistant",
                                                           content=request.message)
        run = self.client.beta.threads.runs.create(thread_id=thread.id,
                                                   assistant_id=assistant.id,
                                                   model="gpt-4o")
        while run.status == "queued" or run.status == "in_progress":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            time.sleep(0.1)
        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        ms = []
        for m in messages.data:
            ms.append({
                "id": m.id,
                "message": m.content[0].text.value
            })
        return ResponseT(code=Code.ok,
                         status=Status.ok,
                         data={
                             "thread_id": thread.id,
                             "assistant_id": assistant.id,
                             "messages": [msg for msg in ms]
                         })

    @staticmethod
    def validate_message(message: str) -> ResponseT:
        return ResponseT(
            code=Code.ok,
            status=Status.ok,
            data=message
        )

    def call_validator(self):
        return self.client.post()
