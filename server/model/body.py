from pydantic import BaseModel

class SearchArticles(BaseModel):
    query: str
    start_date: str
    end_date: str
    filters: dict