import json
import os
import requests
from models.article import Article, ArticleManager
from datetime import datetime
from typing import Union

from utilities import Singleton, timeutil

@Singleton
class UnicloudDBArticleManager(ArticleManager):
    
    def insert_article(self, article: Article) -> None:
        res = requests.post(os.getenv('UNI_APP_CLOUD_DB_INSERT_ARTICLE_URL'), json=article.model_dump())
        if res.status_code != 200:
            raise Exception("Couldn't insert article'")

    def get_max_collect_date(self, filters: dict={}) -> Union[datetime, None]:
        res = requests.get(os.getenv('UNI_APP_CLOUD_DB_MAX_COLLECT_DATE_URL'), params=filters)
        data = json.loads(res.text)
        return timeutil.localize_native_dt(datetime.fromtimestamp(data['data']['max_collect_date'])) if data['success'] else None