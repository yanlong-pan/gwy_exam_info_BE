from fastapi import FastAPI
from search_engine.meilisearch.articles import article_manager
from server.model.body import SearchArticles
from server.model.response import Response
from utilities import timeutil
from fastapi import FastAPI, Depends
from server.routes.auth import get_current_client, router as auth_router

app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.post("/search_articles")
async def search_articles(params: SearchArticles, client_id: str = Depends(get_current_client)):
    search_results = article_manager.search_articles(
        query = params.query,
        page = params.page,
        start_date = timeutil.local_dt_str_to_utc_ts(params.start_date) if params.start_date else None,
        end_date = timeutil.local_dt_str_to_utc_ts(params.end_date) if params.end_date else None,
        filters = params.filters,
    )
    return Response(code=1, msg='Success', result=search_results)

@app.get("/search_articles/{id}")
async def search_article(id: str, client_id: str = Depends(get_current_client)):
    doc = dict(article_manager.index.get_document(id))
    doc.pop('_Document__doc')
    return Response(code=1, msg='Success', result=doc)