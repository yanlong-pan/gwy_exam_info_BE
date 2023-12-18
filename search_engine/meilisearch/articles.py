from datetime import datetime
from typing import Union
from pydantic import BaseModel

from search_engine.meilisearch.manager import Manager
from utilities import Singleton, timeutil
class Article(BaseModel):
    id: str
    title: str
    province: str
    exam_type: str
    info_type: str
    collect_date: float  # numeric UNIX timestamp
    human_read_date: str
    html_content: str

@Singleton
class ArticleManager(Manager):

    def __init__(self):
        super().__init__('articles')
        self.index.update_settings({
            'filterableAttributes': ['province', 'exam_type', 'info_type', 'collect_date', 'title', 'human_read_date'],
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
        return timeutil.localize_native_dt(datetime.fromtimestamp(r['hits'][0]['collect_date'])) if r['hits'] else None

    def search_articles(self, query: str, page: Union[str, int], start_date: float, end_date: float, filters: dict={}):
        limit = 20
        offset = (int(page) - 1) * limit
        r: dict = self.index.search(
            query = query,
            opt_params = {
                'offset': offset,
                'limit': limit,
                'filter': [f'collect_date >= {start_date}', f'collect_date <= {end_date}'] + [f'{key}={value}' for key, value in filters.items()],
                'sort': ['collect_date:desc'],
                'attributesToRetrieve': ['id', 'title', 'province', 'exam_type', 'info_type', 'human_read_date']
            }
        )
        return r['hits'] if r['hits'] else None

article_manager = ArticleManager()