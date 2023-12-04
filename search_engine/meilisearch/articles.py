import os
from meilisearch import Client
from pydantic import BaseModel

class Article(BaseModel):
    id: str
    title: str
    province: str
    exam_type: str
    info_type: str
    collect_date: str
    html_content: str

class ArticleManager:
    def __init__(self, client_url: str, master_key: str, index_uid: str):
        self.client = Client(client_url, master_key)
        self.index = self.client.index(uid=index_uid)

    def insert_article(self, article: Article):
        # 使用字典展开将 Article 模型的属性映射到文档字段
        document = {**article.model_dump()}
        self.index.add_documents([document])

    def search_articles(self, query: str):
        # 执行搜索操作
        search_result = self.index.search(query)
        return search_result['hits']
