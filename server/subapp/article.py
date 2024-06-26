from fastapi import FastAPI

from search_engine.meilisearch.articles import MeiliSearchArticleManager
from server.middleware.authentication import auth_middleware
from server.model.body import SearchArticles
from server.model.response import Response
from utilities import timeutil

_subapp_article = FastAPI()
_subapp_article.middleware('http')(auth_middleware)
meilisearch_article_manager = MeiliSearchArticleManager()

@_subapp_article.post("/all")
async def search_articles(params: SearchArticles):
    search_results = meilisearch_article_manager.search_articles(
        query = params.query,
        page = params.page,
        start_date = timeutil.local_dt_str_to_utc_ts(params.start_date) if params.start_date else None,
        end_date = timeutil.local_dt_str_to_utc_ts(params.end_date) if params.end_date else None,
        filters = params.filters,
    )
    return Response(code=1, msg='Success', result=search_results)

@_subapp_article.get("/{id}")
async def search_article(id: str):
    doc = dict(meilisearch_article_manager.index.get_document(id))
    doc.pop('_Document__doc')
    return Response(code=1, msg='Success', result=doc)