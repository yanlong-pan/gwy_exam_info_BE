from typing import TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class Response(BaseModel):
    code: int
    msg: str
    result: T
