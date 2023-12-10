from dotenv import load_dotenv
from fastapi import FastAPI
from search_engine.meilisearch.articles import article_manager
from server.model.body import SearchArticles
from utilities import timeutil
from fastapi import FastAPI, Depends
from server.routes.auth import get_current_client, router as auth_router

load_dotenv()
app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.post("/search_articles")
async def search_articles(params: SearchArticles, client_id: str = Depends(get_current_client)):
    search_results = article_manager.search_articles(
        query = params.query,
        start_date = timeutil.local_dt_str_to_utc_ts(params.start_date),
        end_date = timeutil.local_dt_str_to_utc_ts(params.end_date),
        filters = params.filters,
    )
    return search_results
