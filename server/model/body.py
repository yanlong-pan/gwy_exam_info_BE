from typing import Union
from pydantic import BaseModel

class SearchArticles(BaseModel):
    query: str
    start_date: str = None
    end_date: str = None
    page: Union[int, str]
    filters: dict