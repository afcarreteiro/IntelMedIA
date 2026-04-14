from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth import authenticate_user, create_access_token, get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_access_token(
        data={
            "sub": user["user_id"],
            "username": user["username"],
            "full_name": user["full_name"],
        }
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        user_id=current_user["sub"],
        username=current_user["username"],
        full_name=current_user.get("full_name", current_user["username"]),
    )
