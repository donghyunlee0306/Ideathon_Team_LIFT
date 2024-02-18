from fastapi import FastAPI
from pydantic import BaseModel


class IdeaInput(BaseModel):
    area: str
    member: str
    background: str
    technology: str
    others: str = None
