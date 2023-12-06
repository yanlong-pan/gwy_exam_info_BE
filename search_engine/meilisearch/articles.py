from pydantic import BaseModel

from search_engine.meilisearch.manager import Manager
from utilities import Singleton

class Article(BaseModel):
    id: str
    title: str
    province: str
    exam_type: str
    info_type: str
    collect_date: str
    html_content: str

@Singleton
class ArticleManager(Manager):

    def __init__(self):
        super().__init__('articles')
        self.index.update_settings({
            'filterableAttributes': ['province', 'exam_type', 'info_type', 'collect_date'],
        })
