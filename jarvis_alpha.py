import json
import os
import time
from typing import Optional

import requests
from openai import OpenAI
from pydantic import BaseModel

from response import ResponseT, Code, Status

class Location(BaseModel):
    latitude: int
    longitude: int

class JarvisAlphaRequest(BaseModel):
    """
    Request class for Jarvis Alpha.
    """
    thread_id: Optional[str] = ""
    message: str
    user_agent: str
    location: Location


class JarvisAlphaService:
    BASE_PATH = '/jarvis_alpha'

    ASSISTANT_ID = 'asst_xZJPXwGx0WXa6YO9N36tlmqk'  # Jarvis Alpha v2 🤖
    # INSTRUCTIONS = ('You are Jarvis Alpha, an artificial intelligence specifically'
    #                 'made for Grab, a super-app for ride-hailing, food delivery, '
    #                 'and digital payment services on mobile devices that operates in Indonesia.'
    #                 'You have given an ability to communicate with Google Maps backend, so you'
    #                 'can construct the best response according to users need. Be helpful!')
    INSTRUCTIONS = "You are a helpful assitant whose task is to "

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "get_places_from_text_search",
                "description": "Get list of places from Google Maps API based on given text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Given text to search with Google Maps Text Search API"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_nearby_places",
                "description": "Get nearby places given an exact coordinate",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "integer",
                            "description": "Latitude value"
                        },
                        "longitude": {
                            "type": "integer",
                            "description": "Longitude of a point"
                        }
                    },
                    "required": ["latitude", "longitude"]
                }
            }
        }
    ]

    def __init__(self, client: OpenAI):
        self.client = client

    def chat(self, request: JarvisAlphaRequest) -> ResponseT:
        """
        Chat with Jarvis Alpha.
        If thread_id is not defined in the body, a new thread will be created.

        :param request:
        :return:
        """
        assistant = self.client.beta.assistants.retrieve(assistant_id=self.ASSISTANT_ID)
        if not request.thread_id:
            thread = self.client.beta.threads.create()
        else:
            thread = self.client.beta.threads.retrieve(thread_id=request.thread_id)

        message = self.client.beta.threads.messages.create(thread_id=thread.id,
                                                           role="user",
                                                           content=request.message)

        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )

        while run.status == "queued" or run.status == "in_progress":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            time.sleep(0.1)

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )
            print(messages)
            return ResponseT(
                code=Code.ok,
                status=Status.ok,
                data=messages.data[0].content[0].text.value
            )
        else:
            messages = run.status
            print(messages)


def get_places_from_text_search(query: str):
    try:
        response = requests.post('https://places.googleapis.com/v1/places:searchText',
                                 headers={
                                     'Content-Type': 'application/json',
                                     'X-Goog-Api-Key': os.getenv('GOOGLE_MAPS_API_KEY'),
                                     'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.priceLevel'
                                 },
                                 json={
                                     "textQuery": query
                                 })
        return response
    except Exception as e:
        return str(e)
