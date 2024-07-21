import json
import os
import time
from typing import Optional, Union, Literal
from urllib.parse import quote

import requests
from openai import OpenAI
from pydantic import BaseModel

from response import ResponseT, Code, Status


class Location(BaseModel):
    latitude: float
    longitude: float


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
    ASSISTANT_ID = 'asst_h5ep6J3Mpvx29kO13XBTheKg'  # Jarvis Alpha v4 🤖

    def __init__(self, client: OpenAI):
        self.client = client

    def chat(self, request: JarvisAlphaRequest) -> ResponseT:
        """
        Chat with Jarvis Alpha.
        If thread_id is not defined in the body, a new thread will be created.

        :param request:
        :return:
        """
        try:
            assistant = self.client.beta.assistants.retrieve(assistant_id=self.ASSISTANT_ID)
            if not request.thread_id:
                thread = self.client.beta.threads.create()
            else:
                thread = self.client.beta.threads.retrieve(thread_id=request.thread_id)

            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=json.dumps({
                    "message": request.message,
                    "latitude": request.location.latitude,
                    "longitude": request.location.longitude
                })
            )

            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
            )

            while run.status != 'completed':
                tool_outputs = []
                for tool in run.required_action.submit_tool_outputs.tool_calls:
                    print(f"TO CALL {tool.function.name}")
                    if tool.function.name == "get_nearby_places":
                        arguments = json.loads(tool.function.arguments)
                        call = self.get_nearby_places(arguments.get("latitude"), arguments.get("longitude"))
                        tool_outputs.append({
                            "tool_call_id": tool.id,
                            "output": json.dumps(call)
                        })
                    elif tool.function.name == "get_text_search":
                        arguments = json.loads(tool.function.arguments)
                        call = self.get_text_search(arguments.get("textQuery"))
                        tool_outputs.append({
                            "tool_call_id": tool.id,
                            "output": json.dumps(call)
                        })
                    elif tool.function.name == "get_geocoding":
                        arguments = json.loads(tool.function.arguments)
                        call = self.get_geocoding(arguments.get("address"))
                        tool_outputs.append({
                            "tool_call_id": tool.id,
                            "output": json.dumps(call)
                        })
                    elif tool.function.name == "get_reverse_geocoding":
                        arguments = json.loads(tool.function.arguments)
                        call = self.get_reverse_geocoding(arguments.get("latlng"))
                        tool_outputs.append({
                            "tool_call_id": tool.id,
                            "output": json.dumps(call)
                        })
                    elif tool.function.name == "get_autocomplete":
                        arguments = json.loads(tool.function.arguments)
                        call = self.get_autocomplete(arguments.get("inputstr"))
                        tool_outputs.append({
                            "tool_call_id": tool.id,
                            "output": json.dumps(call)
                        })
                    elif tool.function.name == "get_routes":
                        print("I WAS HERE")
                        arguments = json.loads(tool.function.arguments)
                        call = self.get_routes(arguments.get("originLatLng"),
                                               arguments.get("destinationLatLng"),
                                               arguments.get("travelMode"))
                        tool_outputs.append({
                            "tool_call_id": tool.id,
                            "output": json.dumps(call)
                        })

                print("TOOL OUTPUTS", tool_outputs)

                if tool_outputs:
                    try:
                        run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                            thread_id=thread.id,
                            run_id=run.id,
                            tool_outputs=tool_outputs
                        )
                        print("Tool outputs submitted successfully.")
                    except Exception as e:
                        print("Failed to submit tool outputs:", e)
                else:
                    print("No tool outputs to submit.")

            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                print(messages)
                return ResponseT(
                    code=Code.ok,
                    status=Status.ok,
                    data=json.loads(messages.data[0].content[0].text.value)
                )
            else:
                print(run.required_action.submit_tool_outputs.tool_calls)

        except Exception as e:
            print(e)

    @staticmethod
    def return_success(response: dict):
        response["success"] = "true"
        return response

    @staticmethod
    def return_failed(e: str):
        return {"success": "false",
                "error": e}

    def get_nearby_places(self, latitude: int, longitude: int):
        FIELD_MASK = 'places.displayName,places.formattedAddress'
        MAX_RESULT_COUNT = 3
        RADIUS = 500
        INCLUDED_TYPES = ["restaurant"]
        try:
            response = requests.post('https://places.googleapis.com/v1/places:searchNearby',
                                     headers={
                                         'Content-Type': 'application/json',
                                         'X-Goog-Api-Key': os.getenv('GOOGLE_MAPS_API_KEY'),
                                         'X-Goog-FieldMask': FIELD_MASK
                                     },
                                     json={"includedTypes": INCLUDED_TYPES,
                                           "maxResultCount": MAX_RESULT_COUNT,
                                           "locationRestriction": {
                                               "circle": {
                                                   "center": {
                                                       "latitude": latitude,
                                                       "longitude": longitude},
                                                   "radius": RADIUS
                                               }
                                           }
                                           })
            return self.return_success(response.json())
        except Exception as e:
            print(e)
            return self.return_failed(str(e))

    def get_text_search(self, textQuery: str):
        FIELD_MASK = 'places.displayName,places.formattedAddress'
        try:
            response = requests.post('https://places.googleapis.com/v1/places:searchText',
                                     headers={
                                         'Content-Type': 'application/json',
                                         'X-Goog-Api-Key': os.getenv('GOOGLE_MAPS_API_KEY'),
                                         'X-Goog-FieldMask': FIELD_MASK
                                     },
                                     json={
                                         "textQuery": textQuery
                                     })
            return self.return_success(response.json())
        except Exception as e:
            print(e)
            return self.return_failed(str(e))

    def get_geocoding(self, address: str):
        BASE_LINK = f"https://maps.googleapis.com/maps/api/geocode/json?"
        ADDRESS = f"address={quote(address)}"
        API_KEY = f"key={os.getenv("GOOGLE_MAPS_API_KEY")}"
        try:
            response = requests.post(f"{BASE_LINK}{ADDRESS}&{API_KEY}")
            return self.return_success(response.json())
        except Exception as e:
            return self.return_failed(str(e))

    def get_reverse_geocoding(self, latlng: str):
        BASE_LINK = f"https://maps.googleapis.com/maps/api/geocode/json?"
        LAT_LNG = f"latlng={latlng}"
        API_KEY = f"key={os.getenv("GOOGLE_MAPS_API_KEY")}"
        try:
            response = requests.post(f"{BASE_LINK}{LAT_LNG}&{API_KEY}")
            return self.return_success(response.json())
        except Exception as e:
            return self.return_failed(str(e))

    def get_autocomplete(self, inputstr: str):
        BASE_LINK = "https://places.googleapis.com/v1/places:autocomplete"
        try:
            response = requests.post(BASE_LINK,
                                     headers={
                                         'Content-Type': 'application/json',
                                         'X-Goog-Api-Key': os.getenv('GOOGLE_MAPS_API_KEY'),
                                     },
                                     json={
                                         "input": inputstr
                                     })
            return self.return_success(response.json())
        except Exception as e:
            return self.return_failed(str(e))

    def get_routes(self, originLatLng: str, destinationLatLng: str, travelMode: Union[str, Literal[
        "TWO_WHEELER",
        "TRANSIT",
        "DRIVE"
    ]]):
        BASE_LINK = "https://routes.googleapis.com/directions/v2:computeRoutes"
        FIELD_MASK = 'routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline'
        origin = originLatLng.split(",")
        originLat, originLng = float(origin[0]), float(origin[1])
        destination = destinationLatLng.split(",")
        destinationLat, destinationLng = float(destination[0]), float(destination[1])
        try:
            response = requests.post(BASE_LINK,
                                     headers={
                                         'Content-Type': 'application/json',
                                         'X-Goog-Api-Key': os.getenv('GOOGLE_MAPS_API_KEY'),
                                         'X-Goog-FieldMask': FIELD_MASK,
                                     },
                                     json={
                                         "origin": {
                                             "location": {
                                                 "latLng": {
                                                     "latitude": originLat,
                                                     "longitude": originLng
                                                 }
                                             }
                                         },
                                         "destination": {
                                             "location": {
                                                 "latLng": {
                                                     "latitude": destinationLat,
                                                     "longitude": destinationLng
                                                 }
                                             }
                                         },
                                         "travelMode": travelMode,
                                         # "computeAlternativeRoutes": False,
                                         # "routeModifiers": {
                                         #     "avoidTolls": False,
                                         #     "avoidHighways": False,
                                         #     "avoidFerries": False
                                         # },
                                         "languageCode": "en-US",
                                         "units": "METRIC"
                                     })
            return self.return_success(response.json())
        except Exception as e:
            return self.return_failed(str(e))
