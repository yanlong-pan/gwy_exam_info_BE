import os
from meilisearch import Client
from pydantic import BaseModel
from typing import TypeVar

# 使用 TypeVar 来定义泛型 T
T = TypeVar('T', bound=BaseModel)

class IndexManager(object):
    def __init__(self,
        index_uid: str,
        client_url: str = os.environ.get('MEILISEARCH_URL', 'http://localhost:7700'),
        master_key: str = os.environ.get('MEILISEARCH_MASTER_KEY')
    ):
        self.index_uid = index_uid
        self.client = Client(client_url, master_key)
        self.index = self.client.index(uid=self.index_uid)
