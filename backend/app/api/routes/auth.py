from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.core.security import authenticate_user, create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
async def login(body: LoginRequest):
    if not authenticate_user(body.username, body.password):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token(body.username)
    return {"access_token": token, "token_type": "bearer"}
