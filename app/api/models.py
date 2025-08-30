# app/api/models.py
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    type: str  # start, chunk, complete, error
    content: str = ""