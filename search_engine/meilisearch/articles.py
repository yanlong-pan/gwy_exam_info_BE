from datetime import datetime
from pydantic import BaseModel
import pytz

from search_engine.meilisearch.manager import Manager
from utilities import Singleton
class Article(BaseModel):
    id: str
    title: str
    province: str
    exam_type: str
    info_type: str
    collect_date: float
    html_content: str

@Singleton
class ArticleManager(Manager):

    def __init__(self):
        super().__init__('articles')
        self.index.update_settings({
            'filterableAttributes': ['province', 'exam_type', 'info_type', 'collect_date', 'title'],
            'sortableAttributes': ['collect_date']
        })
    
    def get_max_collect_date(self, filters: dict={}):
        r: dict = self.index.search(
            query = '*',
            opt_params = {
                'filter': [f'{key}={value}' for key, value in filters.items()],
                'sort': ['collect_date:desc'],
                'attributesToSearchOn': ['collect_date'],
                'limit': 1
            }
        )
        return datetime.utcfromtimestamp(r['hits'][0]['collect_date']).replace(tzinfo=pytz.utc) if r['hits'] else None

article_manager = ArticleManager()