from datetime import datetime
from typing import Optional, Union
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
    apply_deadline: Optional[str]
    html_content: str

@Singleton
class ArticleManager(Manager):

    def __init__(self):
        super().__init__('articles')
        self.index.update_settings({
            'filterableAttributes': ['title', 'province', 'exam_type', 'info_type', 'collect_date', 'apply_deadline'],
            'sortableAttributes': ['collect_date'],
            'rankingRules':[
                "exactness",
                "words",
                "typo",
                "proximity",
                "attribute",
                "sort",
            ],
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

    def search_articles(self, query: str, page: Union[str, int], start_date: float = None, end_date: float = None, filters: dict={}):
        # construct pagination params
        limit = 20
        offset = (int(page) - 1) * limit
        # construct filter array
        filter = []
        for key, value in filters.items():
            if isinstance(value, list):
                filter.append([f'{key}={v}' for v in value])
            else:
                filter.append(f'{key}={value}')
        if not end_date:
            end_date = datetime.now().timestamp()
        filter.append(f'collect_date <= {end_date}')
        if start_date:
            filter.append(f'collect_date >= {start_date}')
        # construct Chinese tokens
        r: dict = self.index.search(
            query = query,
            opt_params = {
                'offset': offset,
                'limit': limit,
                'filter': filter,
                'sort': ['collect_date:desc'],
                'attributesToRetrieve': ['id', 'title', 'province', 'exam_type', 'info_type', 'apply_deadline'],
            }
        )
        return r['hits'] if r['hits'] else None

article_manager = ArticleManager()