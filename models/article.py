from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel
from abc import ABC, abstractmethod

class Article(BaseModel):
    id: str
    title: str
    province: str
    exam_type: str
    info_type: str
    collect_date: float  # numeric UNIX timestamp
    apply_deadline: Optional[str]
    html_content: str

class ArticleManager(ABC):
    
    @abstractmethod
    def insert_article(self, article: Article) -> None:
        pass
    
    @abstractmethod
    def get_max_collect_date(self, filters: dict={}) -> Union[datetime, None]:
        pass