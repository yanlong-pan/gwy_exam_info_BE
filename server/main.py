from fastapi import FastAPI
from fastapi import FastAPI
from server.routes.auth import router as auth_router
from server.subapp.article import _subapp_article

app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.mount('/articles', _subapp_article)
