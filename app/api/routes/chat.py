from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai.chatbot import chat

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    venues: list = []


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Send a message to the Boki AI assistant.

    - **message**: the user's current message
    - **history**: prior turns as [{role, content}] — client manages this

    Returns a text reply plus any venues the AI fetched to answer the question.
    """
    try:
        history = [{"role": m.role, "content": m.content} for m in request.history]
        return await chat(request.message, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
