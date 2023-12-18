from typing import Union
from pydantic import BaseModel

class SearchArticles(BaseModel):
    query: str
    start_date: str
    end_date: str
    page: Union[int, str]
    filters: dict