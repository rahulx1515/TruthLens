from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


class ArticleBase(BaseModel):
    title: Optional[str] = None
    content: str
    url: Optional[str] = None
    domain: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None


class ArticleCreate(ArticleBase):
    pass


class ArticleOut(ArticleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

