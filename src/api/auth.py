from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_db
from db.models.user import User
from schemas.user import TokenResponse, UserResponse
from services.auth import exchange_github_code, get_or_create_user, issue_jwt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github/callback", response_model=TokenResponse)
async def github_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    github_data = await exchange_github_code(code)
    user = await get_or_create_user(db, github_data)
    token = issue_jwt(user)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)
