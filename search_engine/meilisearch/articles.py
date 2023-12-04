from pydantic import BaseModel

from search_engine.meilisearch.manager import Manager

class Article(BaseModel):
    id: str
    title: str
    province: str
    exam_type: str
    info_type: str
    collect_date: str
    html_content: str

class ArticleManager(Manager):
    def __init__(self):
        super().__init__('articles')
