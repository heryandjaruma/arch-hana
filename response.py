from enum import Enum, IntEnum
from typing import Union

from pydantic import BaseModel


class Status(str, Enum):
    ok = "OK"
    error = "ERROR"
    bad_request = "BAD_REQUEST"
    unauthorized = "UNAUTHORIZED"
    not_found = "NOT_FOUND"
    internal_server_error = "INTERNAL_SERVER_ERROR"


class Code(IntEnum):
    ok = 200
    created = 201
    bad_request = 400
    unauthorized = 401
    not_found = 404
    internal_server_error = 500


class ResponseT(BaseModel):
    code: Code
    status: Status
    data: Union[None | str | dict | list]
