import threading
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
    _instance_lock = threading.Lock()
    _instance = None

    def __init__(self):
        super().__init__('articles')
        self.index.update_settings({
            'filterableAttributes': ['province', 'exam_type', 'info_type', 'collect_date'],
        })

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance