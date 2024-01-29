import json
import os
import requests
from models.article import Article, ArticleManager
from datetime import datetime
from typing import Union

from utilities import Singleton, loggers, timeutil

@Singleton
class UnicloudDBArticleManager(ArticleManager):

    def check_article_existence_by_title(self, article_title) -> bool:
        check_res = requests.get(os.getenv('UNI_APP_CLOUD_DB_CHECK_ARTICLE_EXISTENCE'), params={'article_title': article_title})
        if check_res.status_code == 200:
            data = json.loads(check_res.text)
            if data['success']:
                return True
            else:
                loggers.debug_file_logger.debug(data['data']['message'])
                return False

    def insert_article(self, article: Article) -> None:
        insert_res = requests.post(os.getenv('UNI_APP_CLOUD_DB_INSERT_ARTICLE_URL'), json=article.model_dump())
        if insert_res.status_code == 200:
            loggers.debug_file_logger.debug(json.loads(insert_res.text)['data']['message'])

    def get_max_collect_date(self, filters: dict={}) -> Union[datetime, None]:
        res = requests.get(os.getenv('UNI_APP_CLOUD_DB_MAX_COLLECT_DATE_URL'), params=filters)
        data = json.loads(res.text)
        return timeutil.localize_native_dt(datetime.fromtimestamp(data['data']['max_collect_date'])) if data['success'] else None