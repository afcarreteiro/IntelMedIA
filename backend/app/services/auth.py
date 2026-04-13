import secrets

from fastapi import HTTPException, status

from app.schemas.auth import TokenResponse


class AuthService:
    def login(self, username: str, password: str) -> TokenResponse:
        if username != "clinician" or password != "intelmedia":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
        return TokenResponse(access_token=secrets.token_urlsafe(32))
