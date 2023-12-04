import os
from meilisearch import Client
from pydantic import BaseModel
from typing import Type, TypeVar

# 使用 TypeVar 来定义泛型 T
T = TypeVar('T', bound=BaseModel)

class Manager:
    def __init__(self,
        index_uid: str,
        client_url: str = os.environ.get('MEILISEARCH_URL', 'http://localhost:7700'),
        master_key: str = os.environ.get('MEILISEARCH_MASTER_KEY')
    ):
        self.index_uid = index_uid
        self.client = Client(client_url, master_key)
        self.index = self.client.index(uid=self.index_uid)

    def insert_document(self, document: T):
        # 使用字典展开将 document 模型的属性映射到文档字段
        document = {**document.model_dump()}
        self.index.add_documents([document])

    def search_documents(self, query: str):
        # 执行搜索操作
        search_result = self.index.search(query)
        return search_result['hits']