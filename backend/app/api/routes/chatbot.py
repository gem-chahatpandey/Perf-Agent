from pydantic import BaseModel
from fastapi import APIRouter, Depends
from app.services.rag.chat import chat_service
from app.core.security import get_current_user

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    run_id: str | None = None
    history: list[dict] | None = None


@router.post("/chat")
async def chat(body: ChatRequest, _user: str = Depends(get_current_user)):
    result = await chat_service.ask(
        question=body.question,
        run_id=body.run_id,
        history=body.history,
    )
    return result
