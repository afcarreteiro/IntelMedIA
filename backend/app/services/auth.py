import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings


security = HTTPBearer()

VALID_CLINICIANS = {
    "clinician": {
        "password": "intelmedia",
        "full_name": "Dr. Sofia Almeida",
    },
    "drsilva": {
        "password": "doctor123",
        "full_name": "Dr. Tiago Silva",
    },
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload.update({"exp": int(expire.timestamp())})

    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(
        settings.jwt_secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).digest()
    return f"{_encode(payload_bytes)}.{_encode(signature)}"


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload_segment, signature_segment = credentials.credentials.split(".", maxsplit=1)
        payload_bytes = _decode(payload_segment)
        provided_signature = _decode(signature_segment)
        expected_signature = hmac.new(
            settings.jwt_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(provided_signature, expected_signature):
            raise ValueError("Invalid signature")

        payload = json.loads(payload_bytes.decode("utf-8"))
        if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("Token expired")

        return payload
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = VALID_CLINICIANS.get(username)
    if user and user["password"] == password:
        return {
            "user_id": username,
            "username": username,
            "full_name": user["full_name"],
        }
    return None


def get_current_user(payload: dict = Depends(verify_token)) -> dict:
    return payload


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")
